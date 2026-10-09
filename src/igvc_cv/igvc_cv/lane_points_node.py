#!/usr/bin/env python3

import math
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


class LanePointsNode(Node):
    def __init__(self):
        super().__init__("lane_points_node")

        self.declare_parameter("image_topic", "/zed/zed_node/rgb/color/rect/image")
        self.declare_parameter("cloud_topic", "/zed/zed_node/point_cloud/cloud_registered")
        self.declare_parameter("points_topic", "/lanes/points")
        self.declare_parameter("debug_topic", "/lanes/debug_image")

        # Image filtering
        self.declare_parameter("roi_top_fraction", 0.40)
        self.declare_parameter("min_lightness", 130)
        self.declare_parameter("max_saturation", 170)
        
        # Blur
        self.declare_parameter("blur_kernel_size", 11)
        self.declare_parameter("blur_sigma", 0.0)

        # Canny / Hough
        self.declare_parameter("canny_low", 50)
        self.declare_parameter("canny_high", 150)
        self.declare_parameter("hough_threshold", 25)
        self.declare_parameter("hough_min_line_length", 35)
        self.declare_parameter("hough_max_line_gap", 30)
        self.declare_parameter("line_sample_step_px", 5)
        

        # 3D filtering
        self.declare_parameter("min_range_m", 0.3)
        self.declare_parameter("max_range_m", 5.0)
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
        self.mask_pub = self.create_publisher(Image, "/lanes/debug_mask", 10)
        self.blur_pub = self.create_publisher(Image, "/lanes/debug_blur", 10)
        self.edges_pub = self.create_publisher(Image, "/lanes/debug_edges", 10)
        self.hough_pub = self.create_publisher(Image, "/lanes/debug_hough", 10)

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

        self.get_logger().info("lane_points_node started")

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

        line_points, line_mask = self.detect_lane_line_pixels(bgr, cloud_msg)

        min_range = float(self.get_parameter("min_range_m").value)
        max_range = float(self.get_parameter("max_range_m").value)
        max_abs = float(self.get_parameter("max_abs_xyz_m").value)
        max_points = int(self.get_parameter("max_points").value)

        r = np.linalg.norm(line_points, axis=1)
        keep = (
            np.all(np.isfinite(line_points), axis=1)
            & (r >= min_range)
            & (r <= max_range)
            & np.all(np.abs(line_points) <= max_abs, axis=1)
        )
        points = line_points[keep]

        if len(points) > max_points:
            points = points[np.random.choice(len(points), max_points, replace=False)]

        self.publish_points(cloud_msg.header, points.tolist())

        debug_msg = self.bridge.cv2_to_imgmsg(line_mask.astype(np.uint8) * 255, encoding="mono8")
        debug_msg.header = cloud_msg.header
        self.debug_pub.publish(debug_msg)

        self.get_logger().info(
            f"lane debug: mask_px={len(line_points)}, points={len(points)}"
        )
        
    def publish_debug_image(self, pub, img: np.ndarray, frame_id: str = "camera"):
        msg = self.bridge.cv2_to_imgmsg(img, encoding="mono8" if len(img.shape) == 2 else "bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        pub.publish(msg)

    def detect_lane_line_pixels(self, bgr: np.ndarray, cloud_msg) -> Tuple[List[Tuple[int, int]], np.ndarray]:
        xyz_mat = self.cloud_to_xyz_matrix(cloud_msg)
        xyz_diff_mat = np.diff(xyz_mat, axis=0)
        dzdr_mat = xyz_diff_mat[:,:,2] / np.sqrt(xyz_diff_mat[:,:,0]**2 + xyz_diff_mat[:,:,1]**2)
        
        h, w = bgr.shape[:2]

        roi_top = int(h * float(self.get_parameter("roi_top_fraction").value))
        roi_bottom = int(h * 0.90) # TODO: Replace with variable
        min_lightness = int(self.get_parameter("min_lightness").value)
        max_saturation = int(self.get_parameter("max_saturation").value)

        hls = cv2.cvtColor(bgr, cv2.COLOR_BGR2HLS)
        lightness = hls[:, :, 1]
        saturation = hls[:, :, 2]

        mask = np.zeros((h, w), dtype=np.uint8)
        mask[(lightness >= min_lightness) & (saturation <= max_saturation)] = 255
        mask[roi_top:roi_bottom, :] = 0

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        self.publish_debug_image(self.mask_pub, mask)

        ch, cw = xyz_mat.shape[:2]
        color_mask = cv2.resize(mask, (cw, ch), interpolation=cv2.INTER_NEAREST) > 0

        z_mask = xyz_mat[:, :, 2] < 1  # TODO: Replace with variable

        dz_mask = np.zeros((ch, cw), dtype=bool)
        dz_mask[1:] = np.abs(dzdr_mat) < 1  # TODO: Replace with variable

        line_mask = color_mask & z_mask & dz_mask
        line_mask[:int(ch * roi_frac_top)] = False
        line_mask[int(ch * 0.90):] = False

        line_points = xyz_mat[line_mask]
        return line_points, line_mask

    def cloud_to_xyz_matrix(self, cloud_msg: PointCloud2) -> np.ndarray:
        """Return an (H, W, 3) array where [i][j] is the XYZ point at pixel row i, column j."""
        pts = point_cloud2.read_points(
            cloud_msg,
            field_names=("x", "y", "z"),
            skip_nans=False,
            reshape_organized_cloud=True,
        )
        return np.stack([pts["x"], pts["y"], pts["z"]], axis=-1).astype(np.float32)

    def publish_points(self, header, points: List[Tuple[float, float, float]]):
        msg = point_cloud2.create_cloud_xyz32(header, points)
        self.points_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LanePointsNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()