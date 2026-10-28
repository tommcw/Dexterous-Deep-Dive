from ultralytics import YOLO



"""
Save a video with the predictions, used for testing model accuracy on a test video
Code from Ultralytics
https://docs.ultralytics.com/tasks/detect
"""


model_str = input("Example model: yolo11n.pt\nSelect model from folder 'Object_detection_models'\nEnter Model name:")
model_path = ("Object_detection_models/",model_str)

video_str = input("Select video from folder'videos/raw'\n Enter Video File:")
video_path = ("videos/raw", video_str)

model = YOLO(model_path)
results = model(video_path , save= True, show = True)