# VisDrone-YOLO：无人机航拍目标检测与跟踪系统

<p align="center">
  <img src="thesis_figures/val_batch0_pred.jpg" width="70%" alt="检测效果">
</p>

<p align="center">
  <strong>YOLOv8s</strong> · <strong>ByteTrack</strong> · <strong>VisDrone2019</strong> · <strong>Gradio</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10-blue" alt="Python">
  <img src="https://img.shields.io/badge/PyTorch-2.11-red" alt="PyTorch">
  <img src="https://img.shields.io/badge/Ultralytics-YOLOv8-orange" alt="YOLOv8">
  <img src="https://img.shields.io/badge/mAP50-0.3292-brightgreen" alt="mAP">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">
</p>

---

## 📖 项目简介

本科毕业设计项目。基于 YOLOv8s 深度学习模型与 ByteTrack 多目标跟踪算法，针对无人机航拍场景下目标极小、密集、遮挡严重的特点，构建了一套从训练到部署的完整检测跟踪系统。

> 航拍视角下，一辆车可能只有十几个像素。不能把地面检测模型直接搬过来用——得针对航拍场景做专门的设计和训练。

---

## ✨ 核心特性

- **YOLOv8s 检测** — Anchor-Free 解耦头 + C2f 模块，专为小目标优化
- **ByteTrack 跟踪** — 两阶段匹配策略，低分框不丢弃，遮挡场景跟踪更稳定
- **Gradio Web 交互** — 上传视频，选择类别，调节置信度，一键输出标注结果
- **10 类航拍目标** — 行人、骑车人、自行车、轿车、面包车、卡车、三轮车、篷车、公交车、摩托车
- **单卡推理** — RTX 3060 Laptop (6GB) 即可实时运行

---

## 📊 数据集

[VisDrone2019-DET](http://aiskyeye.com/) 由天津大学发布，是无人机航拍目标检测的基准数据集。

| 分割 | 图片数 | 平均目标数/图 | 特点 |
|------|--------|--------------|------|
| 训练集 | 6,471 | 77.0 | 多城市场景，日夜混合 |
| 验证集 | 548 | 49.3 | 独立城市，分布不同 |
| 测试集 | 1,610 | 71.1 | 官方评测集 |

> ⚠️ 数据集文件较大（约 1.8GB），需从 [VisDrone 官网](http://aiskyeye.com/) 下载后放入 datasets/VisDrone/ 目录。

---

## 🎯 实验结果

| 指标 | 验证集 | 测试集 |
|------|--------|--------|
| **mAP50** | 0.4064 | **0.3292** |
| **mAP50-95** | 0.2411 | 0.1909 |
| **Precision** | 0.5125 | 0.4593 |
| **Recall** | 0.3944 | 0.3429 |
| **F1** | — | 0.3927 |

> 数值看似不高，但在航拍极端条件下（目标普遍 < 32×32 像素），已能支撑实际应用。

---

## 🏗️ 系统架构

`
 ┌─────────────────────────────────────────┐
 │              表现层 (Gradio)              │
 │   视频上传 · 类别选择 · 置信度调节 · 结果回显  │
 └─────────────────┬───────────────────────┘
                   │
 ┌─────────────────▼───────────────────────┐
 │           业务逻辑层 (推理调度)             │
 │    GPU 加速 · 视频编解码 · 结果后处理        │
 └─────────────────┬───────────────────────┘
                   │
 ┌─────────────────▼───────────────────────┐
 │      算法核心层 (YOLOv8 + ByteTrack)      │
 │   端到端目标检测 · 跨帧目标 ID 关联          │
 └─────────────────────────────────────────┘
`

**处理流程**：上传视频 → 选类别 + 调阈值 → 逐帧检测 → ByteTrack 关联 → 渲染标注 → 输出视频

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- CUDA 12.x（推荐）或 CPU
- NVIDIA GPU（推荐 RTX 3060 及以上）

### 安装

\\\ash
pip install ultralytics gradio opencv-python torch
\\\

### 下载模型权重

从 [Ultralytics Releases](https://github.com/ultralytics/assets/releases) 下载 yolov8s.pt 放入项目根目录，或使用已训练的 est.pt。

### 运行

\\\ash
# 训练模型
python train.py

# 评估模型
python evaluate.py

# 启动 Web 检测界面
python app.py
\\\

---

## 📁 项目结构

\\\
VisDrone_Project/
├── app.py                  # Gradio Web 应用入口
├── train.py                # YOLOv8 训练脚本
├── detect.py               # 目标检测推理
├── evaluate.py             # 模型评估（mAP / PR / F1）
├── run_all.py              # 一键运行全流程
├── compare_experiments.py  # 实验对比分析
├── generate_data_report.py # 数据集统计报告
├── datasets/VisDrone/      # 数据集目录（需自行下载）
├── thesis_figures/         # 论文图表（PR 曲线、混淆矩阵等）
├── runs/                   # 训练/检测输出（已 gitignore）
├── 毕业论文_完整版.md        # 毕业论文章节
├── 毕业论文_完整版.docx      # 论文 Word 版
└── README.md
\\\

---

## 📈 训练可视化

| 图表 | 说明 |
|------|------|
| esults.png | 训练 loss 与 mAP 收敛曲线 |
| confusion_matrix.png | 10 类混淆矩阵分析 |
| BoxPR_curve.png | Precision-Recall 平衡曲线 |
| BoxF1_curve.png | F1-置信度曲线 |
| al_batch*_pred.jpg | 验证集预测效果可视化 |

详见 [VISUALIZATION_EXPLANATION.md](VISUALIZATION_EXPLANATION.md)

---

## 🛠️ 技术栈

| 组件 | 方案 |
|------|------|
| 深度学习框架 | PyTorch 2.11 + Ultralytics YOLOv8 |
| 目标检测 | YOLOv8s (22.5M 参数) |
| 多目标跟踪 | ByteTrack |
| Web 界面 | Gradio |
| 图像处理 | OpenCV, Pillow |
| 硬件加速 | CUDA 12.8 |

---

## 📝 论文

详见 毕业论文_完整版.md（章节完整版）与 毕业论文_完整版.docx（排版定稿）。

---

## 📄 License

MIT © 2026
