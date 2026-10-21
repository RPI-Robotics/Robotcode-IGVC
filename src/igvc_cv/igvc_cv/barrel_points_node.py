#!/usr/bin/env python3

from typing import List, Tuple

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import Image, PointCloud2
from sensor_msgs_py import point_cloud2

from igvc_cv.cloud_utils import read_cloud_points, scale_uvs_to_cloud


class BarrelPointsNode(Node):
    def __init__(self):
        super().__init__("barrel_points_node")

        self.declare_parameter("image_topic", "/zed/zed_node/rgb/color/rect/image")
        self.declare_parameter("cloud_topic", "/zed/zed_node/point_cloud/cloud_registered")
        self.declare_parameter("points_topic", "/obstacles/barrel_points")
        self.declare_parameter("debug_topic", "/obstacles/debug_image")
        self.declare_parameter("mask_topic", "/obstacles/debug_mask")

        # Orange color threshold (OpenCV HSV: hue 0-179)
        self.declare_parameter("roi_top_fraction", 0.20)
        self.declare_parameter("hue_min", 5)
        self.declare_parameter("hue_max", 22)
        self.declare_parameter("min_saturation", 120)
        self.declare_parameter("min_value", 80)

        # Mask cleanup. The close kernel is large so the orange bands of a
        # barrel merge across its white stripes into one blob.
        self.declare_parameter("open_kernel_size", 5)
        self.declare_parameter("close_kernel_size", 15)
        self.declare_parameter("min_blob_area_px", 300)

        # 3D filtering
        self.declare_parameter("sample_step_px", 4)
        self.declare_parameter("min_range_m", 0.3)
        self.declare_parameter("max_range_m", 8.0)
        self.declare_parameter("max_abs_xyz_m", 20.0)
        self.declare_parameter("max_points", 3000)

        self.bridge = CvBridge()

        self.points_pub = self.create_publisher(
            PointCloud2,
            self.get_parameter("points_topic").value,
            10,
        )
        self.debug_pub = self.create_publisher(
            Image,
            self.get_parameter("debug_topic").value,
            10,
        )
        self.mask_pub = self.create_publisher(
            Image,
            self.get_parameter("mask_topic").value,
            10,
        )

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        self.image_sub = Subscriber(
            self,
            Image,
            self.get_parameter("image_topic").value,
            qos_profile=sensor_qos,
        )
        self.cloud_sub = Subscriber(
            self,
            PointCloud2,
            self.get_parameter("cloud_topic").value,
            qos_profile=sensor_qos,
        )

        self.sync = ApproximateTimeSynchronizer(
            [self.image_sub, self.cloud_sub],
            queue_size=20,
            slop=0.25,
        )
        self.sync.registerCallback(self.callback)

        self.get_logger().info("barrel_points_node started")

    def callback(self, image_msg: Image, cloud_msg: PointCloud2):
        try:
            bgr = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn(f"Image conversion failed: {exc}")
            self.publish_points(cloud_msg.header, [])
            return

        if cloud_msg.height <= 1:
            self.get_logger().warn("PointCloud2 is not organized; cannot UV-index it")
            self.publish_points(cloud_msg.header, [])
            return

        image_h, image_w = bgr.shape[:2]

        mask = self.detect_orange_mask(bgr)
        self.publish_mask(mask, image_msg.header)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = float(self.get_parameter("min_blob_area_px").value)
        sample_step = max(1, int(self.get_parameter("sample_step_px").value))

        debug = bgr.copy()
        all_points: List[Tuple[float, float, float]] = []
        barrel_count = 0

        for contour in contours:
            if cv2.contourArea(contour) < min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            blob_uvs = self.sample_blob_pixels(mask, x, y, w, h, sample_step)
            blob_uvs_cloud = scale_uvs_to_cloud(
                blob_uvs,
                image_w,
                image_h,
                cloud_msg.width,
                cloud_msg.height,
            )
            blob_points = read_cloud_points(
                cloud_msg,
                blob_uvs_cloud,
                float(self.get_parameter("min_range_m").value),
                float(self.get_parameter("max_range_m").value),
                float(self.get_parameter("max_abs_xyz_m").value),
                self.get_logger(),
            )

            # No valid depth means it is out of range or a false positive.
            if not blob_points:
                continue

            barrel_count += 1
            all_points.extend(blob_points)

            dist = float(np.median([np.linalg.norm(p) for p in blob_points]))
            cv2.rectangle(debug, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(
                debug,
                f"{dist:.1f} m",
                (x, max(0, y - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        max_points = int(self.get_parameter("max_points").value)
        if len(all_points) > max_points:
            idx = np.linspace(0, len(all_points) - 1, max_points).astype(np.int32)
            all_points = [all_points[i] for i in idx]

        self.publish_points(cloud_msg.header, all_points)

        debug_msg = self.bridge.cv2_to_imgmsg(debug, encoding="bgr8")
        debug_msg.header = image_msg.header
        self.debug_pub.publish(debug_msg)

        self.get_logger().info(
            f"barrel debug: barrels={barrel_count}, points={len(all_points)}"
        )

    def detect_orange_mask(self, bgr: np.ndarray) -> np.ndarray:
        h = bgr.shape[0]
        roi_top = int(h * float(self.get_parameter("roi_top_fraction").value))

        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([
            int(self.get_parameter("hue_min").value),
            int(self.get_parameter("min_saturation").value),
            int(self.get_parameter("min_value").value),
        ], dtype=np.uint8)
        upper = np.array([
            int(self.get_parameter("hue_max").value),
            255,
            255,
        ], dtype=np.uint8)

        mask = cv2.inRange(hsv, lower, upper)
        mask[:roi_top, :] = 0

        open_k = max(1, int(self.get_parameter("open_kernel_size").value))
        close_k = max(1, int(self.get_parameter("close_kernel_size").value))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((open_k, open_k), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((close_k, close_k), np.uint8))

        return mask

    def sample_blob_pixels(
        self,
        mask: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
        step: int,
    ) -> List[Tuple[int, int]]:
        sub = mask[y:y + h:step, x:x + w:step]
        vs, us = np.nonzero(sub)
        return [(int(x + u * step), int(y + v * step)) for u, v in zip(us, vs)]

    def publish_mask(self, mask: np.ndarray, header):
        msg = self.bridge.cv2_to_imgmsg(mask, encoding="mono8")
        msg.header = header
        self.mask_pub.publish(msg)

    def publish_points(self, header, points: List[Tuple[float, float, float]]):
        msg = point_cloud2.create_cloud_xyz32(header, points)
        self.points_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BarrelPointsNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
