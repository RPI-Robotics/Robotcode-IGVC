"""Export trained weights for deployment.

Run on the Jetson itself for --format engine: TensorRT engines are tied to the
GPU and TensorRT version they were built on.

Usage:
    python3 scripts/export.py models/best.pt --format engine
    python3 scripts/export.py models/best.pt --format onnx
"""
import argparse

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("weights")
    parser.add_argument("--format", choices=["engine", "onnx"], default="engine")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--half", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    out = YOLO(args.weights).export(format=args.format, imgsz=args.imgsz, half=args.half)
    print(f"Exported to {out}")


if __name__ == "__main__":
    main()
