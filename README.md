# 基于 YOLOv8 + ByteTrack 的无人机航拍目标检测与跟踪系统

> 🎓 本科毕业设计 | 智能科学与技术 | 2026

基于 YOLOv8 深度学习框架与 ByteTrack 多目标跟踪算法，在 VisDrone 无人机航拍数据集上构建的端到端检测与跟踪系统，搭载 Gradio Web 交互界面。

## ✨ 特性

- **YOLOv8s 目标检测** — 10 类航拍目标（行人、车辆、自行车等），mAP50 0.3292
- **ByteTrack 多目标跟踪** — 两阶段匹配，稳定处理遮挡与密集场景
- **Gradio Web 界面** — 上传视频、选择类别、调节置信度，一键输出标注视频
- **单 GPU 推理** — RTX 3060 Laptop (6GB) 即可实时运行

## 🏗️ 系统架构

\\\
表现层 (Gradio Web) → 业务逻辑层 (推理调度) → 算法核心层 (YOLOv8 + ByteTrack)
\\\

## 📊 实验结果

| 指标 | 验证集 | 测试集 |
|------|--------|--------|
| mAP50 | 0.4064 | 0.3292 |
| mAP50-95 | 0.2411 | 0.1909 |
| Precision | 0.5125 | 0.4593 |
| Recall | 0.3944 | 0.3429 |

## 🚀 快速开始

### 环境

- Python 3.10+
- PyTorch 2.11 + CUDA
- ultralytics
- Gradio

### 安装

\\\ash
pip install ultralytics gradio opencv-python
\\\

下载模型权重与 VisDrone 数据集（见下方链接），放置到项目目录。

### 运行

\\\ash
# 训练
python train.py

# 评估
python evaluate.py

# 启动 Web 界面
python app.py
\\\

## 📁 项目结构

| 文件/目录 | 说明 |
|-----------|------|
| 	rain.py | 模型训练脚本 |
| detect.py | 目标检测推理 |
| evaluate.py | 模型评估脚本 |
| pp.py | Gradio Web 应用入口 |
| un_all.py | 一键运行全流程 |
| datasets/VisDrone/ | VisDrone 数据集目录 |
| 	hesis_figures/ | 论文图表（PR曲线、混淆矩阵等） |
| uns/ | 训练/检测输出结果 |

## 📦 模型权重

YOLOv8s 预训练权重可从 [Ultralytics Releases](https://github.com/ultralytics/assets/releases) 下载。

VisDrone2019-DET 数据集可从 [VisDrone 官网](http://aiskyeye.com/) 获取。

## 📄 论文

详见 毕业论文_完整版.md / 毕业论文_完整版.docx

## 📝 License

MIT
