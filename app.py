import gradio as gr
from ultralytics import YOLO
import os
import torch
import cv2
from pathlib import Path
from datetime import datetime

# ---------- 模型发现 ----------
PROJECT_ROOT = r"D:\project\VisDrone_Project"

def find_models():
    """自动发现所有已训练的模型权重"""
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

# 默认加载最佳模型
MODELS = find_models()
if not MODELS:
    raise FileNotFoundError("未找到任何已训练的模型权重! 请先运行 train.py 训练模型")

DEFAULT_MODEL = list(MODELS.keys())[0]
model = YOLO(MODELS[DEFAULT_MODEL])
CLASS_NAMES = [model.names[i] for i in sorted(model.names.keys())]
CLASS_NAME_TO_INDEX = {name: idx for idx, name in model.names.items()}

# ---------- 视频转换 ----------
def convert_to_mp4(source_path):
    """尝试转换为 H.264 MP4, 失败则返回原文件"""
    if not source_path or not os.path.exists(source_path):
        return source_path
    dest_path = os.path.splitext(source_path)[0] + "_web.mp4"
    if os.path.exists(dest_path):
        return dest_path
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(source_path)
        clip.write_videofile(dest_path, codec="libx264", audio_codec="aac", logger=None)
        clip.close()
        return dest_path
    except Exception:
        return source_path  # 转换失败则直接用原文件

def find_saved_video(save_dir, source_path):
    """在保存目录中定位处理后的视频"""
    if not save_dir or not os.path.exists(save_dir):
        return None
    video_name = os.path.basename(source_path)
    base_name = os.path.splitext(video_name)[0]

    # 直接匹配
    candidate = os.path.join(save_dir, video_name)
    if os.path.exists(candidate):
        return candidate

    # 尝试不同扩展名
    for ext in [".mp4", ".avi", ".mov", ".mkv"]:
        alt = os.path.splitext(candidate)[0] + ext
        if os.path.exists(alt):
            return alt

    # 深层搜索
    for root, _, files in os.walk(save_dir):
        for f in files:
            name, ext = os.path.splitext(f)
            if name.startswith(base_name) and ext.lower() in [".mp4", ".avi", ".mov", ".mkv"]:
                return os.path.join(root, f)
    return None

# ---------- 核心处理 ----------
def process_video(video_path, model_name, selected_classes, conf_threshold):
    """处理视频: 根据选择的模型和类别进行检测与跟踪"""
    if video_path is None:
        return None, "请先上传视频文件"

    use_gpu = torch.cuda.is_available()
    device = "cuda:0" if use_gpu else "cpu"
    device_name = "GPU" if use_gpu else "CPU"

    # 切换模型
    global model
    if model_name in MODELS:
        model = YOLO(MODELS[model_name])

    class_indices = None
    class_info = "所有类别"
    if selected_classes and len(selected_classes) > 0:
        class_indices = [CLASS_NAME_TO_INDEX.get(name) for name in selected_classes
                        if name in CLASS_NAME_TO_INDEX]
        class_info = ", ".join(selected_classes)

    start_time = datetime.now()
    results = model.track(
        source=video_path,
        tracker="bytetrack.yaml",
        conf=conf_threshold,
        classes=class_indices if class_indices else None,
        save=True,
        device=device,
        project="runs/detect",
        name="track",
        exist_ok=True,
        verbose=False,
    )
    elapsed = (datetime.now() - start_time).total_seconds()

    save_dir = str(results[0].save_dir)
    output_path = find_saved_video(save_dir, video_path)

    if output_path is None:
        return None, f"处理完成但未找到输出文件, 请检查 {save_dir}"

    output_path = convert_to_mp4(output_path)
    info = f"[{device_name}] 检测类别: {class_info} | 置信度: {conf_threshold} | 耗时: {elapsed:.1f}s"
    return output_path, info

# ---------- Gradio 界面 ----------
with gr.Blocks(title="VisDrone 无人机航拍目标检测与跟踪系统") as demo:
    gr.Markdown("""
    <h1 style='text-align: center;'>VisDrone 无人机航拍目标检测与跟踪系统</h1>
    <h3 style='text-align: center;'>基于 YOLOv8 + ByteTrack | 支持可选类别识别与实时结果回显</h3>
    """)

    with gr.Row():
        with gr.Column(scale=2):
            video_input = gr.Video(label="上传无人机航拍视频", sources=["upload"])

            model_select = gr.Dropdown(
                choices=list(MODELS.keys()),
                value=DEFAULT_MODEL,
                label="选择模型",
                info="不同实验训练的模型"
            )

            class_select = gr.CheckboxGroup(
                choices=CLASS_NAMES,
                label="选择要识别的目标类别 (可多选)",
                info="不选择则识别所有类别"
            )

            confidence_slider = gr.Slider(
                minimum=0.1, maximum=1.0, value=0.25, step=0.05,
                label="最低置信度阈值",
                info="调整检测结果的灵敏度"
            )

            process_button = gr.Button("开始检测与跟踪", variant="primary")

        with gr.Column(scale=3):
            video_output = gr.Video(label="识别结果视频")
            stats_box = gr.Textbox(label="系统提示", interactive=False)

    gr.Markdown("""
    **系统说明**
    - **模型底座**: YOLOv8 深度学习网络
    - **训练数据**: VisDrone 复杂航拍数据集 (10类目标)
    - **跟踪算法**: ByteTrack 多目标跟踪技术
    - 上传视频后, 系统会自动返回带检测框和跟踪ID的处理结果
    """)

    process_button.click(
        fn=process_video,
        inputs=[video_input, model_select, class_select, confidence_slider],
        outputs=[video_output, stats_box]
    )

if __name__ == "__main__":
    demo.launch(share=False, inbrowser=True)
