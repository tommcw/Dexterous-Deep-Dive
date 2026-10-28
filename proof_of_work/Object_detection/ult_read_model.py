import cv2
from ultralytics import YOLO
import time

cap = cv2.VideoCapture(0)#, cv2.CAP_DSHOW

if not cap.isOpened():
    print("DirectShow failed to open camera.")
else:
    model = YOLO("weights.pt")
    class_names = model.names
    predictions = model.track(source= 0, show =True, stream = True)

    while True:
        ret, frame = cap.read()

        if not ret:
            print("fail")
            break

        for result in predictions:
            short_box = []
            bbox_list = result.boxes.xywh.tolist()          # bounding boxes all objects, you can also get xywh with boxes.xywh
            


            clss_list = result.boxes.cls.int().tolist()     # class index all objects
            conf_list = result.boxes.conf.tolist()          # confidence list all objects
            for box, cls, conf in zip(bbox_list, clss_list, conf_list): #iterate over each bbox, cls and conf
                if conf > 0.5:
                    
                    print(f"Bounding box: {box}, Class index: {cls}, Class name:{class_names[cls]}, Confidence: {conf}, Time {time.monotonic()}")
                    #... any downstream tasks
            # save results to a         

            


#frame = cap.read()

#model = YOLO("weights.pt")
#class_names = model.names
# results = model.predict(source=frame, show=True, save=True)

# for result in results:
#     bbox_list = result.boxes.xyxy.tolist()          # bounding boxes all objects, you can also get xywh with boxes.xywh
#     clss_list = result.boxes.cls.int().tolist()     # class index all objects
#     conf_list = result.boxes.conf.tolist()          # confidence list all objects
#     for box, cls, conf in zip(bbox_list, clss_list, conf_list): #iterate over each bbox, cls and conf
#         print(f"Bounding box: {box}, Class index: {cls}, Class name:{class_names[cls]}, Confidence: {conf}")
#         #... any downstream tasks
