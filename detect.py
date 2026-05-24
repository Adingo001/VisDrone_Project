"""
VisDrone 检测脚本 (增强版)
支持图像/视频检测、模型选择、结果可视化
"""
from ultralytics import YOLO
import torch
import os
import argparse
from pathlib import Path

PROJECT_ROOT = r"D:\project\VisDrone_Project"

def find_models():
    models = {}
    search_dirs = [
        os.path.join(PROJECT_ROOT, "runs", "train"),
        os.path.join(PROJECT_ROOT, "runs", "detect", "runs", "train"),
    ]
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
        for exp_name in os.listdir(base_dir):
            weight_dir = os.path.join(base_dir, exp_name, "weights")
            best_pt = os.path.join(weight_dir, "best.pt")
            if os.path.exists(best_pt):
                models[exp_name] = best_pt
    return models

def main():
    parser = argparse.ArgumentParser(description="VisDrone YOLOv8 检测")
    parser.add_argument("--source", "-s", type=str, required=True, help="输入图片/视频路径")
    parser.add_argument("--model", "-m", type=str, default=None, help="模型名称, 默认使用最佳模型")
    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值 (默认 0.25)")
    parser.add_argument("--track", action="store_true", help="启用 ByteTrack 多目标跟踪")
    parser.add_argument("--list-models", action="store_true", help="列出可用模型")
    args = parser.parse_args()

    models = find_models()
    if not models:
        print("未找到任何已训练的模型, 请先运行 train.py")
        return

    if args.list_models:
        print("可用模型:")
        for name, path in models.items():
            print(f"  {name}: {path}")
        return

    # 选择模型
    if args.model and args.model in models:
        model_path = models[args.model]
    else:
        model_path = list(models.values())[0]
        if args.model:
            print(f"未找到模型 '{args.model}', 使用默认模型")

    print(f"模型: {model_path}")
    print(f"输入: {args.source}")
    print(f"设备: {'GPU' if torch.cuda.is_available() else 'CPU'}")

    model = YOLO(model_path)

    if args.track:
        results = model.track(
            source=args.source,
            tracker="bytetrack.yaml",
            conf=args.conf,
            save=True,
            device=0 if torch.cuda.is_available() else "cpu",
        )
    else:
        results = model.predict(
            source=args.source,
            conf=args.conf,
            save=True,
            device=0 if torch.cuda.is_available() else "cpu",
        )

    print(f"检测完成! 结果保存在: {results[0].save_dir}")

if __name__ == "__main__":
    main()
