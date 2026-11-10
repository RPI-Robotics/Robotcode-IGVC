# igvc_cv/yolo

Object detection (traffic drums, ramps) for the IGVC robot. Consumed by
`igvc_cv/yolo_detect_node.py`.

    yolo/
      datasets/cone_ramp_seg/      polygon labels, classes: drum, ramp  (preferred)
      datasets/cone_ramp_detect/   original Roboflow box labels (v1, YOLOv8)
      datasets/archive/            original Roboflow zip
      models/                      trained weights for the ROS node (git-ignored)
      scripts/train.py             training entry point
      scripts/export.py            ONNX / TensorRT export
      runs/                        ultralytics output (git-ignored); runs/seg-prev = earlier run

Datasets and weights are git-ignored. Source: Roboflow igvc-tu8v8/cone_ramp_detection v1 (CC BY 4.0).

## Workflow

### 1. Train (dev machine with an NVIDIA GPU)

    python3 -m venv ~/yolo-venv            # needs: apt install python3-venv
    ~/yolo-venv/bin/pip install "ultralytics==8.4.*" pyyaml
    cd src/igvc_cv/yolo
    ~/yolo-venv/bin/python scripts/train.py --task seg --device 0

Results go to `runs/seg/` (overwritten each run), `best.pt` is copied to
`models/best.pt` automatically, and test-split metrics are printed at the end.
Use `--batch 8` if CUDA runs out of memory, and keep `--workers` low on WSL.

### 2. Deploy on the Jetson

1. Check the JetPack version: `cat /etc/nv_tegra_release` (R35 = JetPack 5, R36 = JetPack 6).
2. Install NVIDIA's Jetson PyTorch wheel for that JetPack (the regular pip torch
   is CPU-only on aarch64), then `pip install "ultralytics==8.4.*"` with the
   same version as training. Install into the Python that ROS uses, not a venv.
   **Keep ROS's `cv_bridge` working:** ultralytics pulls in NumPy 2 and OpenCV 5, which
   crash the node (`KeyError: 16`, or "compiled using NumPy 1.x"). Install with
   `pip install "numpy<2" "opencv-python-headless<5"` (or `--no-deps` for ultralytics
   and rely on the system `python3-opencv`), then check
   `python3 -c "import cv2, numpy; from cv_bridge import CvBridge"` before launching.
3. Copy `models/best.pt` into this repo's `src/igvc_cv/yolo/models/` on the robot.
4. Build the TensorRT engine **on the Jetson** (engines are tied to its GPU and TensorRT version):
   `python3 scripts/export.py models/best.pt --format engine` -> `models/best.engine`
5. `colcon build --packages-select igvc_cv`, then `ros2 launch igvc_cv igvc_cv.launch.py`.
   With `model_path: ""` the node uses `best.engine` when present, otherwise `best.pt`.
   `use_yolo:=false` disables the detector.

## Topics

- `/objects/points` (PointCloud2): points of `costmap_classes` (default drum only), used by nav2.
- `/objects/detections` (vision_msgs/Detection3DArray): all classes, with 3D center/size.
- `/objects/debug_image` (Image): annotated camera image.
