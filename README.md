<div align="center">

# 🚁 VisDrone-YOLO

### 基于 YOLOv8 + ByteTrack 的无人机航拍目标检测与跟踪系统

<p>
  <img src="thesis_figures/val_batch0_pred.jpg" width="75%" alt="VisDrone 检测效果">
</p>

<p>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://pytorch.org/"><img src="https://img.shields.io/badge/PyTorch-2.11-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch"></a>
  <a href="https://docs.ultralytics.com/"><img src="https://img.shields.io/badge/Ultralytics-YOLOv8-111F68?logo=ultralytics" alt="YOLOv8"></a>
  <a href="https://www.gradio.app/"><img src="https://img.shields.io/badge/UI-Gradio-F97316?logo=gradio&logoColor=white" alt="Gradio"></a>
  <br>
  <img src="https://img.shields.io/badge/mAP50-0.3292-success" alt="mAP50">
  <img src="https://img.shields.io/badge/mAP50--95-0.1909-blue" alt="mAP50-95">
  <img src="https://img.shields.io/badge/dataset-VisDrone2019--DET-00ADD8" alt="VisDrone">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

[English](README.md) | 中文

</div>

---

## 📖 项目简介

无人机航拍视角下，一辆车可能只有十几个像素。目标极小、分布密集、遮挡频繁——地面检测模型不能直接搬过来用。

本项目针对航拍场景的极端条件，基于 **YOLOv8s** 检测器与 **ByteTrack** 多目标跟踪算法，在 VisDrone2019-DET 数据集上完成了从训练、评估到部署的完整流程，并构建了 Gradio Web 交互界面。

**本科毕业设计项目** | 智能科学与技术 | 2026

---

## ✨ 亮点

- **Anchor-Free 检测** — YOLOv8s 解耦头 + C2f 模块，专为小目标特征提取优化
- **两阶段跟踪** — ByteTrack 低分框二次匹配，遮挡场景下轨迹不中断
- **Web 一键体验** — 上传视频 → 选类别 → 调阈值 → 输出标注视频
- **10 类航拍目标** — pedestrian · people · bicycle · car · van · truck · tricycle · awning-tricycle · bus · motor
- **单卡即用** — RTX 3060 Laptop 6GB 可完成训练和实时推理

---

## 🚀 快速开始

### 环境

`ash
# Python 3.10+ with CUDA 12.x
pip install ultralytics gradio opencv-python torch
`

### 数据集

从 [VisDrone 官网](http://aiskyeye.com/) 下载 VisDrone2019-DET，解压到 datasets/VisDrone/：

`
datasets/VisDrone/
├── images/
│   ├── train/    # 6,471 张训练图像
│   ├── val/      # 548 张验证图像
│   └── test/     # 1,610 张测试图像
└── labels/
    ├── train/
    └── val/
`

### 运行

`ash
# 训练（200 epochs，自动混合精度）
python train.py

# 模型评估
python evaluate.py

# 启动 Web 检测界面
python app.py
`

打开浏览器访问 http://localhost:7860，上传航拍视频即可体验。

---

## 📊 实验结果

| 指标 | 验证集 | 测试集 |
|:------|:-------:|:-------:|
| **mAP@0.5** | 0.4064 | **0.3292** |
| **mAP@0.5:0.95** | 0.2411 | 0.1909 |
| Precision | 0.5125 | 0.4593 |
| Recall | 0.3944 | 0.3429 |
| F1 Score | — | 0.3927 |

> 航拍场景下目标普遍 < 32×32 像素，以上指标已能支撑实际感知应用。

### 训练收敛曲线

<p align="center">
  <img src="thesis_figures/results.png" width="80%" alt="训练曲线">
</p>

### 检测效果

| 真实标注 | 模型预测 |
|:---:|:---:|
| <img src="thesis_figures/val_batch0_labels.jpg" width="100%"> | <img src="thesis_figures/val_batch0_pred.jpg" width="100%"> |
| <img src="thesis_figures/val_batch1_labels.jpg" width="100%"> | <img src="thesis_figures/val_batch1_pred.jpg" width="100%"> |
| <img src="thesis_figures/val_batch2_labels.jpg" width="100%"> | <img src="thesis_figures/val_batch2_pred.jpg" width="100%"> |

### 可视化分析

| 图表 | 说明 |
|:------|:------|
| confusion_matrix.png | 10 类混淆矩阵 |
| BoxPR_curve.png | Precision-Recall 曲线 |
| BoxF1_curve.png | F1-置信度曲线 |
| BoxP_curve.png | Precision-置信度曲线 |
| BoxR_curve.png | Recall-置信度曲线 |

---

## 🏗️ 系统架构

`
┌──────────────────────────────────────────────┐
│              表现层 · Gradio                  │
│   视频上传 · 类别选择 · 置信度调节 · 结果回显    │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│           业务逻辑层 · 推理调度                 │
│   GPU 加速 · 视频编解码 · ByteTrack 关联 · 渲染  │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│       算法核心层 · YOLOv8 + ByteTrack          │
│   端到端目标检测 · 两阶段目标关联 · 轨迹管理      │
└──────────────────────────────────────────────┘
`

### 推理流程

`
上传视频 → 逐帧解码 → YOLOv8 检测 → ByteTrack 关联 ID
    → 绘制检测框 + ID → H.264 编码 → 返回结果视频
`

---

## 📁 项目结构

`
VisDrone_Project/
├── app.py                  # Gradio Web 入口
├── train.py                # 训练脚本（200 epochs, AdamW, AMP）
├── detect.py               # 检测推理
├── evaluate.py             # 模型评估（mAP / PR / F1 / 混淆矩阵）
├── run_all.py              # 一键全流程
├── compare_experiments.py  # 实验对比
├── generate_data_report.py # 数据集统计报告
├── datasets/VisDrone/      # 数据集（需自行下载）
├── thesis_figures/         # 论文可视化图表
├── 毕业论文_完整版.md        # 论文章节
├── 毕业论文_完整版.docx      # 论文排版定稿
└── README.md
`

---

## 🛠️ 技术栈

| 组件 | 方案 | 说明 |
|:------|:------|:------|
| 语言 | Python 3.10 | — |
| 深度学习 | PyTorch 2.11 + Ultralytics | YOLOv8s, 22.5M 参数 |
| 检测模型 | YOLOv8s | Anchor-Free 解耦头 |
| 跟踪算法 | ByteTrack | 两阶段 IoU 匹配 |
| Web 界面 | Gradio | 零前端代码 |
| 图像处理 | OpenCV, Pillow | 视频编解码 |
| 优化器 | AdamW + CosineAnnealing | lr=0.001 |
| 数据增强 | Mosaic + RandAugment | 在线增强 |
| 硬件加速 | CUDA 12.8 + AMP | 混合精度训练 |

---

## 📝 论文

- **章节版**: 毕业论文_完整版.md
- **排版定稿**: 毕业论文_完整版.docx
- **数据集统计**: VisDrone_数据统计报告.docx
- **技术文档**: VisDrone_毕业设计技术文档.docx

---

## 📄 License

MIT © 2026 — 详见 [LICENSE](LICENSE)

---

<div align="center">
  <sub>Built with ❤️ for drone vision</sub>
</div>
