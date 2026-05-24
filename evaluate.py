"""
VisDrone 测试集定量评估脚本
对训练好的模型在 VisDrone test 集上运行评估,生成指标对比表
"""
from ultralytics import YOLO
import torch
import os
import json
import csv
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = r"D:\project\VisDrone_Project"
TRAIN_DIR = os.path.join(PROJECT_ROOT, "runs", "train")
# 兼容旧的嵌套路径
ALT_TRAIN_DIR = os.path.join(PROJECT_ROOT, "runs", "detect", "runs", "train")

def find_experiments():
    """找到所有已训练的模型权重"""
    experiments = []
    for base_dir in [TRAIN_DIR, ALT_TRAIN_DIR]:
        if not os.path.exists(base_dir):
            continue
        for exp_name in os.listdir(base_dir):
            weight_dir = os.path.join(base_dir, exp_name, "weights")
            best_pt = os.path.join(weight_dir, "best.pt")
            if os.path.exists(best_pt):
                experiments.append({
                    "name": exp_name,
                    "path": best_pt,
                    "base_dir": base_dir
                })
    return experiments

def evaluate_model(model_path, exp_name):
    """在 test 集上评估模型"""
    print(f"\n评估: {exp_name} ({model_path})")
    try:
        model = YOLO(model_path)
        results = model.val(
            data="VisDrone.yaml",
            split="test",
            imgsz=640,
            batch=16,
            device=0 if torch.cuda.is_available() else "cpu",
            verbose=False,
        )
        return {
            "experiment": exp_name,
            "mAP50": round(float(results.box.map50), 4),
            "mAP50_95": round(float(results.box.map), 4),
            "precision": round(float(results.box.mp), 4),
            "recall": round(float(results.box.mr), 4),
            "f1": round(2 * float(results.box.mp) * float(results.box.mr) /
                       (float(results.box.mp) + float(results.box.mr) + 1e-8), 4),
            "model_path": model_path,
        }
    except Exception as e:
        print(f"  评估失败: {e}")
        return None

def main():
    print(f"设备: {'GPU' if torch.cuda.is_available() else 'CPU'}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    experiments = find_experiments()
    if not experiments:
        print("未找到已训练的模型,请先运行 train.py")
        return

    print(f"找到 {len(experiments)} 个实验:")
    for exp in experiments:
        print(f"  - {exp['name']}")

    results = []
    for exp in experiments:
        r = evaluate_model(exp["path"], exp["name"])
        if r:
            results.append(r)

    if not results:
        print("所有评估均失败")
        return

    # 按 mAP50 排序
    results.sort(key=lambda x: x["mAP50"], reverse=True)

    # 打印结果表
    print(f"\n{'='*80}")
    print(f"{'实验名':<25} {'mAP50':>8} {'mAP50-95':>10} {'Precision':>10} {'Recall':>8} {'F1':>8}")
    print(f"{'-'*80}")
    for r in results:
        print(f"{r['experiment']:<25} {r['mAP50']:>8.4f} {r['mAP50_95']:>10.4f} "
              f"{r['precision']:>10.4f} {r['recall']:>8.4f} {r['f1']:>8.4f}")
    print(f"{'='*80}")

    # 保存 CSV
    output_csv = os.path.join(PROJECT_ROOT, "evaluation_results.csv")
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["experiment", "mAP50", "mAP50_95",
                                                "precision", "recall", "f1", "model_path"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n结果已保存: {output_csv}")

    # 保存 JSON
    output_json = os.path.join(PROJECT_ROOT, "evaluation_results.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已保存: {output_json}")

if __name__ == "__main__":
    main()
