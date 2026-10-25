import cv2
from ultralytics import YOLO

model = YOLO("model_storage/hand_objectsV7.pt")

def detect_objects(frame):
    """
    Synchronously processes a single frame. 
    Blocks execution until inference is complete, then returns structured data.
    """
    # Run inference (stream=False forces synchronous blocking behavior)
    results = model(frame, verbose=False)
        
    # Access the first result object
    result = results[0]
    boxes = result.boxes
        
    detections = []
        
    for box in boxes:
        # 1. Extract location coordinates
        x1, y1, x2, y2 = box.xyxy[0].tolist()
            
        # 2. Extract confidence
        confidence = float(box.conf[0])
            
        # 3. Extract object class name
        class_id = int(box.cls[0])
        object_name = model.names[class_id]
            
        # Build structured dictionary for this object
        detections.append({
            "object_name": object_name,
            "object_num" :class_id,
            "confidence": round(confidence, 4),
            "xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]
        })
            
    # Get the plotted image matrix directly from the result object
    annotated_frame = result.plot()
        
    # Return both the text data and the visual frame to the caller
    return detections, annotated_frame

def compare_objects(data):
    ''' 
    compares two objects.
    If two objects intersect, test  if one is a hand and the other an object.
    send command to pick up object
    
    TODO: 
        command to hand needs to be sent on a positive match
    
    '''
            
    num_items = len(data)
            
    if num_items <=1: #there are no objects to check 
        return
            
    for box_i in data:
        data.remove(box_i)

        box_i_x1, box_i_y1, box_i_x2, box_i_y2 = box_i["xyxy"]

        box_i_mid_x = (box_i_x1 + box_i_x2)/2
        box_i_mid_y = (box_i_y1 + box_i_y2)/2

        for box_j in data:
            
            if box_i == box_j:
                continue

            box_j_x1, box_j_y1, box_j_x2, box_j_y2 = box_j["xyxy"]
                   
            box_j_mid_x = (box_j_x1 + box_j_x2)/2           
            box_j_mid_y = (box_j_y1 + box_j_y2)/2

            dx = abs(box_i_mid_x - box_j_mid_x)
            dy = abs(box_i_mid_y - box_j_mid_y)
                
            if dx <=2 and dy <= 3:
                print("I dont think youre supposed to be here")# they might be the same object
                continue

            intersect_x1 = max(box_i_x1,box_j_x1)
            intersect_y1 = max(box_i_y1,box_j_y1)
            intersect_x2 = min(box_i_x2,box_j_x2)
            intersect_y2 = min(box_i_y2,box_j_y2)

                    
            if (intersect_x1 > intersect_x2) or (intersect_y1 > intersect_y2): 
                    #boxes do not intersect
                    continue

            i_is_hand = box_i["object_num"] == 0
            j_is_hand = box_j["object_num"] == 0

            i_is_egg = box_i["object_num"] ==1
            j_is_egg = box_j["object_num"] ==1 

            i_is_ping_pong = box_i["object_num"]==2
            j_is_ping_pong = box_j["object_num"]==2

            if (i_is_egg and j_is_hand) or (j_is_egg and i_is_hand):
                #hand manipulation to begin
                print("pick up egg") 

            if (i_is_ping_pong and j_is_hand) or (j_is_ping_pong and i_is_hand):
                #hand manipulation to begin
                print("pick up ping pong")
  
    return

def __main__():
        """
        Test loop to run detection model on video
        """
        video_file = "video/raw/front_pickup_test.mov" # video test file location 
        cap = cv2.VideoCapture(video_file)

        
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            # --- SYNCHRONOUS STEP 1: Call the object detection function ---
            # Your script will pause here until 'detect_objects' returns its values
            data, annotated_image = detect_objects(frame)

            # --- SYNCHRONOUS STEP 2: Run logic on the object detection data ---
            compare_objects(data)

            # --- SYNCHRONOUS STEP 3: Display the frame ---
            cv2.imshow("Test video", annotated_image)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

__main__()