# -*- coding: utf-8 -*-
"""
VisDrone 批量训练 + 评估 + 报告 一键脚本
用法: python run_all.py [--skip-train]
"""
import os, sys, argparse, csv, json
from datetime import datetime

os.environ["YOLO_CONFIG_DIR"] = "D:/project/VisDrone_Project/.ultralytics"
os.environ["YOLO_OFFLINE"] = "true"

PROJECT_ROOT = r"D:\project\VisDrone_Project"

EXPERIMENTS = [
    ("exp_yolov8s_640",  "yolov8s.pt", 640,  200, 8,  "YOLOv8s 640 (主实验)"),
    ("exp_yolov8n_640",  "yolov8n.pt", 640,  200, 16, "YOLOv8n 640 (轻量对比)"),
    ("exp_yolov8s_1280", "yolov8s.pt", 1280, 200, 4,  "YOLOv8s 1280 (高分对比)"),
    ("exp_yolov8m_640",  "yolov8m.pt", 640,  200, 4,  "YOLOv8m 640 (深模型对比)"),
]

def run_experiment(exp_name, model_name, imgsz, epochs, batch, desc):
    from ultralytics import YOLO
    import torch

    print(f"\n{'='*60}")
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] {exp_name}: {desc}")
    print(f"  model={model_name}, imgsz={imgsz}, epochs={epochs}, batch={batch}")
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
        close_mosaic=0,
        cos_lr=True,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        warmup_epochs=3,
        amp=True,
        plots=True,
        save=True,
    )
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] {exp_name} DONE\n")

def evaluate_all():
    from ultralytics import YOLO
    import torch

    models = {}
    for base_dir in ["runs/train", "runs/detect/runs/train"]:
        bp = os.path.join(PROJECT_ROOT, base_dir)
        if not os.path.exists(bp):
            continue
        for exp_name in os.listdir(bp):
            wp = os.path.join(bp, exp_name, "weights")
            best_pt = os.path.join(wp, "best.pt")
            if os.path.exists(best_pt):
                models[exp_name] = best_pt

    print(f"\n评估 {len(models)} 个模型: {list(models.keys())}")
    results_list = []

    for exp_name, model_path in models.items():
        print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] 评估: {exp_name}")
        model = YOLO(model_path)
        results = model.val(
            data="VisDrone.yaml",
            split="test",
            imgsz=640,
            batch=16,
            device=0 if torch.cuda.is_available() else "cpu",
            workers=0,
            verbose=False,
        )
        r = {
            "experiment": exp_name,
            "mAP50": round(float(results.box.map50), 4),
            "mAP50_95": round(float(results.box.map), 4),
            "precision": round(float(results.box.mp), 4),
            "recall": round(float(results.box.mr), 4),
        }
        r["f1"] = round(2 * r["precision"] * r["recall"] / (r["precision"] + r["recall"] + 1e-8), 4)
        results_list.append(r)
        print(f"    mAP50={r['mAP50']} mAP50-95={r['mAP50_95']} P={r['precision']} R={r['recall']}")

    if results_list:
        results_list.sort(key=lambda x: x["mAP50"], reverse=True)
        csv_path = os.path.join(PROJECT_ROOT, "evaluation_results.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["experiment", "mAP50", "mAP50_95", "precision", "recall", "f1"])
            w.writeheader()
            w.writerows(results_list)
        print(f"\n结果已保存: {csv_path}")

    return results_list

def generate_report(results):
    lines = []
    lines.append(f"# VisDrone 实验对比报告\n")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("## Test 集指标排名\n")
    lines.append("| 排名 | 实验名 | mAP50 | mAP50-95 | Precision | Recall | F1 |")
    lines.append("|------|--------|-------|----------|-----------|--------|----|")

    for i, r in enumerate(results):
        medal = ["🥇","🥈","🥉"][i] if i < 3 else str(i+1)
        lines.append(f"| {medal} | {r['experiment']} | {r['mAP50']} | {r['mAP50_95']} | {r['precision']} | {r['recall']} | {r['f1']} |")

    if len(results) >= 2:
        base = results[-1]
        best = results[0]
        improvement = (best["mAP50"] - base["mAP50"]) / base["mAP50"] * 100 if base["mAP50"] > 0 else 0
        lines.append(f"\n## 关键结论\n")
        lines.append(f"- 最佳模型: **{best['experiment']}** (mAP50={best['mAP50']})")
        lines.append(f"- 相比基线 ({base['experiment']}) 提升: {improvement:+.1f}%")

    report_path = os.path.join(PROJECT_ROOT, "experiment_comparison.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"报告已生成: {report_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-train", action="store_true", help="跳过训练,仅评估")
    parser.add_argument("--exp", type=str, default=None, help="指定单个实验名")
    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print(f"  VisDrone 全流程脚本")
    print(f"  开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")

    if not args.skip_train:
        for exp_name, model_name, imgsz, epochs, batch, desc in EXPERIMENTS:
            if args.exp and args.exp != exp_name:
                continue
            try:
                run_experiment(exp_name, model_name, imgsz, epochs, batch, desc)
            except Exception as e:
                print(f"  {exp_name} 失败: {e}")

    print(f"\n{'='*60}")
    print(f"  训练完成, 开始评估...")
    print(f"{'='*60}")

    results = evaluate_all()
    if results:
        generate_report(results)

    print(f"\n{'#'*60}")
    print(f"  全部完成! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

if __name__ == "__main__":
    main()
