# 基于 YOLOv8 的 VisDrone 无人机航拍目标检测与跟踪系统

> 生成时间: 2026-05-12 17:44:04

## 1. 项目概述

本项目基于 YOLOv8 深度学习框架，在 VisDrone 无人机航拍数据集上训练目标检测模型，并结合 ByteTrack 多目标跟踪算法，构建了可交互的 Web 检测系统。

- **框架**: PyTorch 2.11 + YOLOv8 (ultralytics)
- **算法**: YOLOv8s 目标检测 + ByteTrack 多目标跟踪
- **数据集**: VisDrone2019-DET (训练 6471 / 验证 548 / 测试 1610)
- **硬件**: NVIDIA RTX 3060 Laptop (6GB VRAM)
- **交互界面**: Gradio Web 应用，支持选类检测 + 置信度调节

## 2. 数据集分析

VisDrone2019-DET 是无人机视角下的航拍目标检测基准数据集，包含 10 个目标类别：

> pedestrian, people, bicycle, car, van, truck, tricycle, awning-tricycle, bus, motor

| 数据分割 | 图片数 | 平均目标数/图 |
|----------|--------|---------------|
| train | 6471 | 77.0 |
| val | 548 | 49.3 |
| test | 1610 | 71.1 |

**难点分析**: 无人机航拍视角下目标尺度极小（多数 < 32x32 像素），目标密集分布，光照和遮挡变化剧烈，对检测算法提出极高要求。

## 3. 模型配置

- **基础模型**: YOLOv8s (22.5M 参数, 28.5 GFLOPs)
- **优化器**: AdamW, lr=0.001, 余弦退火
- **训练策略**: 200 epochs, Mosaic 增强, 混合精度 (AMP)
- **输入尺寸**: 640x640
- **batch size**: 8

## 4. 实验结果

### 4.1 验证集指标

| 实验 | mAP50 | mAP50-95 | Precision | Recall |
|------|-------|----------|-----------|--------|
| visdrone_exp1 ⭐ | 0.4064 | 0.2411 | 0.5125 | 0.3944 |
| exp_yolov8s_640 | 0.3921 | 0.2317 | 0.5015 | 0.3786 |

### 4.2 测试集指标

| 实验 | mAP50 | mAP50-95 | Precision | Recall | F1 |
|------|-------|----------|-----------|--------|----|
| visdrone_exp1 | 0.3292 | 0.1909 | 0.4593 | 0.3429 | 0.3927 |

**最佳测试结果**: mAP50 = 0.3292, mAP50-95 = 0.1909

## 5. 系统架构

### 三层架构

1. **表现层**: Gradio Web 界面 — 视频上传、类别选择、结果回显
2. **业务逻辑层**: 推理调度 — GPU 加速、视频编解码、结果后处理
3. **算法核心层**: YOLOv8 检测 + ByteTrack 跟踪 — 端到端目标检测与多目标关联

### 处理流程

1. 用户上传航拍视频 → 2. 选择目标类别 + 置信度阈值 → 3. 模型逐帧检测
→ 4. ByteTrack 跨帧关联 ID → 5. 渲染检测框 + ID 标注 → 6. 返回结果视频

## 6. 训练可视化说明

详见 [VISUALIZATION_EXPLANATION.md](VISUALIZATION_EXPLANATION.md)，关键图表：
- `results.png` — 训练 loss 与 mAP 收敛曲线
- `confusion_matrix.png` — 类别混淆分析
- `BoxPR_curve.png` — Precision-Recall 平衡曲线
- `val_batch*_pred.jpg` — 验证集预测可视化

## 7. 技术栈

| 组件 | 方案 |
|------|------|
| 编程语言 | Python 3.10 |
| 深度学习 | PyTorch 2.11 + ultralytics YOLOv8 |
| 跟踪算法 | ByteTrack |
| Web 框架 | Gradio |
| 图像处理 | OpenCV, Pillow |
| 硬件加速 | CUDA 12.8 |

## 8. 总结与展望

本系统完成了从数据准备、模型训练、性能评估到 Web 部署的完整流程。
在 VisDrone 测试集上取得 mAP50 = 0.329 的检测精度，并实现了基于 ByteTrack 的多目标实时跟踪。

**未来改进方向**:
- 增大输入分辨率 (1280+) 以捕获更多小目标细节
- 引入 SAHI 切片推理策略处理超高分辨率航拍图
- 尝试 YOLOv8m/l 等更大模型提升检测精度
- 引入注意力机制 (CBAM/SE) 增强小目标特征提取
