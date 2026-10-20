from ultralytics import YOLO



"""
Save a video with the predictions, used for testing model accuracy on a test video
Code from Ultralytics
https://docs.ultralytics.com/tasks/detect
"""
model = YOLO("handegppbv3.pt")

results = model("IMG_1160.mov", save= True, show = True)