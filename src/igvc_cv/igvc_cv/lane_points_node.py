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

from igvc_cv.cloud_utils import read_cloud_points, scale_uvs_to_cloud


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

        # Mask noise reduction
        self.declare_parameter("morph_kernel_size", 5)
        self.declare_parameter("min_blob_area_px", 100)
        self.declare_parameter("min_blob_elongation", 2.0)

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
        self.declare_parameter("min_line_angle_deg", 20.0)
        self.declare_parameter("max_line_angle_deg", 80.0)

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

        line_uvs_image, debug_img = self.detect_lane_line_pixels(bgr)
        line_uvs_cloud = scale_uvs_to_cloud(
            line_uvs_image,
            image_w,
            image_h,
            cloud_msg.width,
            cloud_msg.height,
        )

        points = read_cloud_points(
            cloud_msg,
            line_uvs_cloud,
            float(self.get_parameter("min_range_m").value),
            float(self.get_parameter("max_range_m").value),
            float(self.get_parameter("max_abs_xyz_m").value),
            self.get_logger(),
        )
        self.publish_points(cloud_msg.header, points)

        debug_msg = self.bridge.cv2_to_imgmsg(debug_img, encoding="bgr8")
        debug_msg.header = image_msg.header
        self.debug_pub.publish(debug_msg)

        self.get_logger().info(
            f"lane debug: lines_uv={len(line_uvs_image)}, points={len(points)}"
        )
        
    def publish_debug_image(self, pub, img: np.ndarray, frame_id: str = "camera"):
        msg = self.bridge.cv2_to_imgmsg(img, encoding="mono8" if len(img.shape) == 2 else "bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        pub.publish(msg)

    def detect_lane_line_pixels(self, bgr: np.ndarray) -> Tuple[List[Tuple[int, int]], np.ndarray]:
        h, w = bgr.shape[:2]

        roi_top = int(h * float(self.get_parameter("roi_top_fraction").value))
        roi_bottom = int(h * 0.90)
        min_lightness = int(self.get_parameter("min_lightness").value)
        max_saturation = int(self.get_parameter("max_saturation").value)

        hls = cv2.cvtColor(bgr, cv2.COLOR_BGR2HLS)
        lightness = hls[:, :, 1]
        saturation = hls[:, :, 2]

        mask = np.zeros((h, w), dtype=np.uint8)
        mask[(lightness >= min_lightness) & (saturation <= max_saturation)] = 255
        mask[:roi_top, :] = 0
        mask[roi_bottom:, :] = 0

        morph_k = max(1, int(self.get_parameter("morph_kernel_size").value))
        kernel = np.ones((morph_k, morph_k), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        mask = self.filter_mask_blobs(mask)

        self.publish_debug_image(self.mask_pub, mask)

        blur_k = int(self.get_parameter("blur_kernel_size").value) if self.has_parameter("blur_kernel_size") else 11
        blur_sigma = float(self.get_parameter("blur_sigma").value) if self.has_parameter("blur_sigma") else 0.0

        if blur_k % 2 == 0:
            blur_k += 1
        blur_k = max(3, blur_k)

        blurred = cv2.GaussianBlur(mask, (blur_k, blur_k), blur_sigma)

        self.publish_debug_image(self.blur_pub, blurred)

        edges = cv2.Canny(
            blurred,
            int(self.get_parameter("canny_low").value),
            int(self.get_parameter("canny_high").value),
        )

        self.publish_debug_image(self.edges_pub, edges)

        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180.0,
            threshold=int(self.get_parameter("hough_threshold").value),
            minLineLength=int(self.get_parameter("hough_min_line_length").value),
            maxLineGap=int(self.get_parameter("hough_max_line_gap").value),
        )

        debug = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        sample_step = max(1, int(self.get_parameter("line_sample_step_px").value))
        max_points = int(self.get_parameter("max_points").value)

        min_angle = float(self.get_parameter("min_line_angle_deg").value)
        max_angle = float(self.get_parameter("max_line_angle_deg").value)

        uvs: List[Tuple[int, int]] = []

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]

                dx = x2 - x1
                dy = y2 - y1
                length = math.hypot(dx, dy)

                angle = abs(math.degrees(math.atan2(dy, dx)))

                # Keep lane-like diagonals, reject horizontal noise and nearly vertical artifacts.
                if angle < min_angle or angle > max_angle:
                    continue

                # Reject very bottom/near-camera noise.
                line_mid_v = 0.5 * (y1 + y2)
                if line_mid_v > h * 0.82:
                    continue

                cv2.line(debug, (x1, y1), (x2, y2), (0, 255, 0), 2)

                samples = max(2, int(length / sample_step))
                for i in range(samples):
                    t = i / float(samples - 1)
                    u = int(round((1.0 - t) * x1 + t * x2))
                    v = int(round((1.0 - t) * y1 + t * y2))

                    if 0 <= u < w and 0 <= v < h:
                        uvs.append((u, v))

        if len(uvs) > max_points:
            idx = np.linspace(0, len(uvs) - 1, max_points).astype(np.int32)
            uvs = [uvs[i] for i in idx]

        self.publish_debug_image(self.hough_pub, debug)

        return uvs, debug

    def filter_mask_blobs(self, mask: np.ndarray) -> np.ndarray:
        """Drop small speckles and round blobs (glare, potholes) that are not line-shaped."""
        min_area = float(self.get_parameter("min_blob_area_px").value)
        min_elongation = float(self.get_parameter("min_blob_elongation").value)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        keep = np.zeros_like(mask)

        for contour in contours:
            if cv2.contourArea(contour) < min_area:
                continue

            _, (rect_w, rect_h), _ = cv2.minAreaRect(contour)
            short_side = min(rect_w, rect_h)
            if short_side > 0 and max(rect_w, rect_h) / short_side < min_elongation:
                continue

            cv2.drawContours(keep, [contour], -1, 255, thickness=cv2.FILLED)

        # AND with the original so holes inside kept blobs stay empty.
        return cv2.bitwise_and(mask, keep)

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