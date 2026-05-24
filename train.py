from ultralytics import YOLO
import torch
import argparse
import os
from datetime import datetime

# 实验配置矩阵：不同模型 + 不同输入尺寸的对比实验
EXPERIMENTS = [
    # (实验名, 模型, imgsz, epochs, batch, 说明)
    ("exp_yolov8n_640",  "yolov8n.pt", 640,  200, 16, "YOLOv8n @ 640 (轻量基准)"),
    ("exp_yolov8s_640",  "yolov8s.pt", 640,  200, 8,  "YOLOv8s @ 640 (原实验升级)"),
    ("exp_yolov8s_1280", "yolov8s.pt", 1280, 200, 4,  "YOLOv8s @ 1280 (高分辨率)"),
    ("exp_yolov8m_640",  "yolov8m.pt", 640,  200, 4,  "YOLOv8m @ 640 (中等模型)"),
]

def run_experiment(exp_name, model_name, imgsz, epochs, batch, description):
    print(f"\n{'='*60}")
    print(f"  实验: {exp_name}")
    print(f"  说明: {description}")
    print(f"  模型: {model_name}, imgsz={imgsz}, epochs={epochs}, batch={batch}")
    print(f"{'='*60}\n")

    model = YOLO(model_name)
    model.train(
        data="VisDrone.yaml",
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=0 if torch.cuda.is_available() else "cpu",
        workers=4,
        project="runs/train",
        name=exp_name,
        exist_ok=True,
        # 关键优化参数
        close_mosaic=0,          # mosaic 增强保持到训练结束
        cos_lr=True,             # 余弦退火学习率
        optimizer="AdamW",       # AdamW 对小目标通常更好
        lr0=0.001,               # 初始学习率
        lrf=0.01,                # 最终学习率倍数
        warmup_epochs=3,
        amp=True,                # 混合精度训练
        plots=True,
        save=True,
    )
    print(f"\n  实验 {exp_name} 完成！\n")

def main():
    parser = argparse.ArgumentParser(description="VisDrone YOLOv8 多实验训练")
    parser.add_argument("--exp", type=str, default=None,
                        help="指定单个实验名运行，不指定则运行全部")
    parser.add_argument("--list", action="store_true",
                        help="列出所有实验配置")
    args = parser.parse_args()

    if args.list:
        print("\n可用实验:")
        for i, (name, model, sz, ep, bs, desc) in enumerate(EXPERIMENTS):
            print(f"  [{i}] {name}: {desc}")
            print(f"      模型={model}, imgsz={sz}, epochs={ep}, batch={bs}")
        return

    print(f"\n设备: {'GPU' if torch.cuda.is_available() else 'CPU'}")
    if torch.cuda.is_available():
        print(f"显存: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for name, model_name, sz, ep, bs, desc in EXPERIMENTS:
        if args.exp and args.exp != name:
            continue
        try:
            run_experiment(name, model_name, sz, ep, bs, desc)
        except Exception as e:
            print(f"  实验 {name} 失败: {e}")
            continue

    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
