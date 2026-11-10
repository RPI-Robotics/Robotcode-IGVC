#!/usr/bin/env python3

import os
from typing import List, Tuple

import cv2
import numpy as np
import rclpy
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import Image, PointCloud2
from sensor_msgs_py import point_cloud2
from vision_msgs.msg import Detection3D, Detection3DArray, ObjectHypothesisWithPose

from igvc_cv.cloud_utils import cloud_to_xyz_matrix


class YoloDetectNode(Node):
    def __init__(self):
        super().__init__("yolo_detect_node")

        self.declare_parameter("image_topic", "/zed/zed_node/rgb/color/rect/image")
        self.declare_parameter("cloud_topic", "/zed/zed_node/point_cloud/cloud_registered")
        self.declare_parameter("points_topic", "/objects/points")
        self.declare_parameter("detections_topic", "/objects/detections")
        self.declare_parameter("debug_topic", "/objects/debug_image")

        # Model
        self.declare_parameter("model_path", "")
        self.declare_parameter("conf", 0.4)
        self.declare_parameter("iou", 0.5)
        self.declare_parameter("imgsz", 640)
        self.declare_parameter("device", "")

        # Only these classes are published to /objects/points (costmap).
        # All classes are published to /objects/detections.
        self.declare_parameter("costmap_classes", ["drum"])

        # 3D filtering
        self.declare_parameter("min_range_m", 0.3)
        self.declare_parameter("max_range_m", 8.0)
        self.declare_parameter("max_abs_xyz_m", 20.0)
        self.declare_parameter("max_points_per_object", 1000)
        self.declare_parameter("mask_erode_px", 2)

        # Imported here so a missing ultralytics fails with a clear error at startup.
        from ultralytics import YOLO

        model_path = self.get_parameter("model_path").value
        if not model_path:
            # Prefer a TensorRT engine (built on the Jetson) over the .pt weights.
            models_dir = os.path.join(get_package_share_directory("igvc_cv"), "models")
            engine = os.path.join(models_dir, "best.engine")
            model_path = engine if os.path.exists(engine) else os.path.join(models_dir, "best.pt")
        self.model = YOLO(model_path)
        self.get_logger().info(f"Loaded model {model_path}: {self.model.names}")

        self.bridge = CvBridge()

        self.points_pub = self.create_publisher(
            PointCloud2, self.get_parameter("points_topic").value, 10
        )
        self.detections_pub = self.create_publisher(
            Detection3DArray, self.get_parameter("detections_topic").value, 10
        )
        self.debug_pub = self.create_publisher(
            Image, self.get_parameter("debug_topic").value, 10
        )

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        self.image_sub = Subscriber(
            self, Image, self.get_parameter("image_topic").value, qos_profile=sensor_qos
        )
        self.cloud_sub = Subscriber(
            self, PointCloud2, self.get_parameter("cloud_topic").value, qos_profile=sensor_qos
        )

        self.sync = ApproximateTimeSynchronizer(
            [self.image_sub, self.cloud_sub],
            queue_size=20,
            slop=0.25,
        )
        self.sync.registerCallback(self.callback)

        self.get_logger().info("yolo_detect_node started")

    def callback(self, image_msg: Image, cloud_msg: PointCloud2):
        try:
            bgr = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warn(f"Image conversion failed: {exc}")
            return

        if cloud_msg.height <= 1:
            self.get_logger().warn("PointCloud2 is not organized; cannot UV-index it")
            return

        result = self.model.predict(
            bgr,
            conf=float(self.get_parameter("conf").value),
            iou=float(self.get_parameter("iou").value),
            imgsz=int(self.get_parameter("imgsz").value),
            device=self.get_parameter("device").value or None,
            verbose=False,
        )[0]

        xyz = cloud_to_xyz_matrix(cloud_msg)
        costmap_classes = set(self.get_parameter("costmap_classes").value)

        detections = Detection3DArray()
        detections.header = cloud_msg.header
        costmap_points: List[Tuple[float, float, float]] = []

        for i in range(0 if result.boxes is None else len(result.boxes)):
            pts = self.object_points(result, i, bgr.shape[:2], xyz)
            if len(pts) == 0:
                continue

            cls_id = int(result.boxes.cls[i])
            cls_name = self.model.names[cls_id]
            score = float(result.boxes.conf[i])

            detections.detections.append(
                self.make_detection(cloud_msg.header, cls_name, score, pts)
            )
            if cls_name in costmap_classes:
                costmap_points.extend(map(tuple, pts.tolist()))

        self.detections_pub.publish(detections)
        self.points_pub.publish(point_cloud2.create_cloud_xyz32(cloud_msg.header, costmap_points))

        debug_msg = self.bridge.cv2_to_imgmsg(result.plot(), encoding="bgr8")
        debug_msg.header = image_msg.header
        self.debug_pub.publish(debug_msg)

        self.get_logger().info(
            f"yolo: detections={len(detections.detections)}, costmap_points={len(costmap_points)}",
            throttle_duration_sec=2.0,
        )

    def object_points(self, result, i: int, image_hw: Tuple[int, int], xyz: np.ndarray) -> np.ndarray:
        """XYZ points of detection i, from its segmentation mask (or its box for detect-only models)."""
        image_h, image_w = image_hw
        cloud_h, cloud_w = xyz.shape[:2]
        sx = cloud_w / float(image_w)
        sy = cloud_h / float(image_h)

        mask = np.zeros((cloud_h, cloud_w), dtype=np.uint8)
        poly = result.masks.xy[i] if result.masks is not None else None
        if poly is not None and len(poly) >= 3:
            poly = poly * np.array([sx, sy])
            cv2.fillPoly(mask, [np.round(poly).astype(np.int32)], 255)
        else:
            x1, y1, x2, y2 = result.boxes.xyxy[i].tolist()
            cv2.rectangle(
                mask,
                (int(x1 * sx), int(y1 * sy)),
                (int(x2 * sx), int(y2 * sy)),
                255,
                thickness=-1,
            )

        # Shrink the mask so edge pixels (whose depth often hits the background) are dropped.
        erode_px = int(self.get_parameter("mask_erode_px").value)
        if erode_px > 0:
            eroded = cv2.erode(mask, np.ones((2 * erode_px + 1, 2 * erode_px + 1), np.uint8))
            if np.any(eroded):  # keep the original for objects too small to survive erosion
                mask = eroded

        pts = xyz[mask > 0]

        min_range = float(self.get_parameter("min_range_m").value)
        max_range = float(self.get_parameter("max_range_m").value)
        max_abs = float(self.get_parameter("max_abs_xyz_m").value)

        r = np.linalg.norm(pts, axis=1)
        keep = (
            np.all(np.isfinite(pts), axis=1)
            & (r >= min_range)
            & (r <= max_range)
            & np.all(np.abs(pts) <= max_abs, axis=1)
        )
        pts = pts[keep]

        max_points = int(self.get_parameter("max_points_per_object").value)
        if len(pts) > max_points:
            pts = pts[np.linspace(0, len(pts) - 1, max_points).astype(np.int64)]
        return pts

    def make_detection(self, header, cls_name: str, score: float, pts: np.ndarray) -> Detection3D:
        det = Detection3D()
        det.header = header

        hyp = ObjectHypothesisWithPose()
        hyp.hypothesis.class_id = cls_name
        hyp.hypothesis.score = score
        det.results.append(hyp)

        lo = pts.min(axis=0)
        hi = pts.max(axis=0)
        center = np.median(pts, axis=0)
        det.bbox.center.position.x = float(center[0])
        det.bbox.center.position.y = float(center[1])
        det.bbox.center.position.z = float(center[2])
        det.bbox.center.orientation.w = 1.0
        det.bbox.size.x = float(hi[0] - lo[0])
        det.bbox.size.y = float(hi[1] - lo[1])
        det.bbox.size.z = float(hi[2] - lo[2])
        return det


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
