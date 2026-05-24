"""
多实验对比报告生成器
读取所有实验的 results.csv, 生成对比图表和汇总表格
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = r"D:\project\VisDrone_Project"

def find_all_experiments():
    """扫描所有训练实验目录"""
    experiments = []
    search_dirs = [
        os.path.join(PROJECT_ROOT, "runs", "train"),
        os.path.join(PROJECT_ROOT, "runs", "detect", "runs", "train"),
    ]
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
        for exp_name in os.listdir(base_dir):
            exp_dir = os.path.join(base_dir, exp_name)
            results_csv = os.path.join(exp_dir, "results.csv")
            if os.path.exists(results_csv):
                experiments.append({
                    "name": exp_name,
                    "dir": exp_dir,
                    "results_csv": results_csv,
                })
    return experiments

def load_results_csv(csv_path):
    """加载 results.csv 并提取最后一个 epoch 的指标"""
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return None
    last = rows[-1]
    return {
        "box_loss": float(last.get("train/box_loss", 0)),
        "cls_loss": float(last.get("train/cls_loss", 0)),
        "dfl_loss": float(last.get("train/dfl_loss", 0)),
        "precision": float(last.get("metrics/precision(B)", 0)),
        "recall": float(last.get("metrics/recall(B)", 0)),
        "mAP50": float(last.get("metrics/mAP50(B)", 0)),
        "mAP50_95": float(last.get("metrics/mAP50-95(B)", 0)),
        "val_box_loss": float(last.get("val/box_loss", 0)),
        "val_cls_loss": float(last.get("val/cls_loss", 0)),
        "val_dfl_loss": float(last.get("val/dfl_loss", 0)),
    }

def load_eval_results():
    """加载测试集评估结果"""
    eval_csv = os.path.join(PROJECT_ROOT, "evaluation_results.csv")
    if not os.path.exists(eval_csv):
        return {}
    eval_map = {}
    with open(eval_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eval_map[row["experiment"]] = row
    return eval_map

def generate_markdown_report():
    """生成 Markdown 格式的对比报告"""
    experiments = find_all_experiments()
    eval_results = load_eval_results()

    if not experiments:
        print("未找到任何实验数据")
        return

    lines = []
    lines.append("# VisDrone 实验对比报告")
    lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 验证集指标 (来自 results.csv)
    lines.append("## 验证集指标 (最终 Epoch)\n")
    lines.append("| 实验名 | mAP50 | mAP50-95 | Precision | Recall | Box Loss | CLS Loss |")
    lines.append("|--------|-------|----------|-----------|--------|----------|----------|")

    for exp in sorted(experiments, key=lambda e: e["name"]):
        results = load_results_csv(exp["results_csv"])
        if results:
            lines.append(
                f"| {exp['name']} "
                f"| {results['mAP50']:.4f} "
                f"| {results['mAP50_95']:.4f} "
                f"| {results['precision']:.4f} "
                f"| {results['recall']:.4f} "
                f"| {results['box_loss']:.4f} "
                f"| {results['cls_loss']:.4f} |"
            )

    # 测试集指标 (来自 evaluate.py)
    if eval_results:
        lines.append("\n## 测试集指标\n")
        lines.append("| 实验名 | mAP50 | mAP50-95 | Precision | Recall | F1 |")
        lines.append("|--------|-------|----------|-----------|--------|----|")
        for name, row in sorted(eval_results.items()):
            lines.append(
                f"| {name} "
                f"| {row['mAP50']} "
                f"| {row['mAP50_95']} "
                f"| {row['precision']} "
                f"| {row['recall']} "
                f"| {row['f1']} |"
            )

    # 分析建议
    lines.append("\n## 分析\n")

    # 找到最佳模型
    best_exp = None
    best_map = 0
    for exp in experiments:
        results = load_results_csv(exp["results_csv"])
        if results and results["mAP50"] > best_map:
            best_map = results["mAP50"]
            best_exp = exp["name"]

    if best_exp:
        lines.append(f"- **最佳模型**: {best_exp} (mAP50={best_map:.4f})")

    # mAP50-95 偏低说明
    lines.append("- VisDrone 数据集小目标占比高, mAP50-95 普遍偏低属于正常现象")
    lines.append("- 如需进一步提升, 建议增大输入分辨率 (1280+) 并尝试 YOLOv8m/l")
    lines.append("- 可考虑使用 SAHI 切片推理策略处理高分辨率航拍图")

    report_path = os.path.join(PROJECT_ROOT, "experiment_comparison.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"报告已生成: {report_path}")
    return report_path

def main():
    report = generate_markdown_report()
    if report:
        with open(report, "r", encoding="utf-8") as f:
            print(f.read())

if __name__ == "__main__":
    main()
