from ultralytics import YOLO
import os

model = YOLO(r'D:\project\VisDrone_Project\runs\detect\runs\train\visdrone_exp1\weights\best.pt')
results = model.track(
    source=r'D:\project\VisDrone_Project\test4.mp4',
    tracker='bytetrack.yaml',
    conf=0.25,
    save=True,
    device='cuda:0',
    verbose=False
)
print('save_dir=', results[0].save_dir)
print('save_path=', getattr(results[0], 'path', 'no path'))
print('save_name=', getattr(results[0], 'save_name', 'no save_name'))
print('output exists=', os.path.exists(results[0].save_dir))
files = os.listdir(results[0].save_dir)
print('files in save_dir=', files)
for f in files:
    print(f, os.path.splitext(f)[1])
