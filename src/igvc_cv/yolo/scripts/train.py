"""Train a YOLOv8 model on one of the datasets in ../datasets.

Output goes to runs/<task>/ (overwritten each run) and best.pt is copied to
models/best.pt for the ROS node.

Usage (from src/igvc_cv/yolo):
    python3 scripts/train.py --task seg
    python3 scripts/train.py --task detect --epochs 100
"""
import argparse
import shutil
from pathlib import Path

import yaml
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
TASKS = {
    "seg": ("cone_ramp_seg", "yolov8n-seg.pt"),
    "detect": ("cone_ramp_detect", "yolov8n.pt"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=TASKS, default="seg")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--device", default=None)
    parser.add_argument("--resume", action="store_true",
                        help="continue runs/<task>/weights/last.pt after an interrupted run")
    args = parser.parse_args()

    dataset, base = TASKS[args.task]
    dataset_dir = ROOT / "datasets" / dataset
    cfg = yaml.safe_load((dataset_dir / "data.yaml").read_text())
    cfg["path"] = str(dataset_dir)  # "path: ." would resolve against the cwd
    (ROOT / "runs").mkdir(exist_ok=True)
    data_yaml = ROOT / "runs" / f"{args.task}_data.yaml"
    data_yaml.write_text(yaml.safe_dump(cfg))

    if args.resume:
        # Resume restores epochs, optimizer and augmentation settings from last.pt.
        YOLO(str(ROOT / "runs" / args.task / "weights" / "last.pt")).train(resume=True)
    else:
        train(args, data_yaml, base)

    best = ROOT / "runs" / args.task / "weights" / "best.pt"
    dest = ROOT / "models" / "best.pt"
    dest.parent.mkdir(exist_ok=True)
    shutil.copy2(best, dest)
    print(f"Copied {best} -> {dest}")

    YOLO(str(dest)).val(
        data=str(data_yaml),
        split="test",
        imgsz=args.imgsz,
        device=args.device,
        project=str(ROOT / "runs"),
        name=f"{args.task}_test",
        exist_ok=True,
    )


def train(args, data_yaml, base):
    model = YOLO(str(ROOT / "runs" / base))  # base weights download here, not into the cwd
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        project=str(ROOT / "runs"),
        name=args.task,
        exist_ok=True,
    )


if __name__ == "__main__":
    main()
