from inspire_rh56dftp import InspireHand, registers
import socket
import time
import threading
import numpy as np 
import matplotlib.pyplot as plt
import cv2
from ultralytics import YOLO

class Hand_manupultion:
    '''
    This class works with the Inspire Hand RH56DFTP.


    
    '''

    def __init__(self):
        self.hand_ip = "192.168.123.210"
        self.fingers = [
            "Pinky",
            "Ring",
            "Middle",
            "Index",
            "Thumb bend",
            "Thumb rotation"
        ]

        self.hand_speed = 100

        self.position = [1000,1000,1000,1000,1000,1000]

        self.sensor_table = {}

        # Thread management flags
        self._is_running = False
        self._thread = None
        self._start_time = None
        self.camera = 2
        self.model = YOLO("model_storage/hand_objectsV7.pt")# "EggPingPongBallv2.pt" 
        self.cap =cv2.VideoCapture(self.camera) # possibly add a setter method to allow for this to be changed


    #############################
    #
    #   getters
    #
    #############################

    def check_ip(self):
        '''Identifies what hand is connected and ensures connection

        TODO: does not check if two hands are connected,         
        '''
        port = 6000
        left_hand_ip = "192.168.123.210"
        right_hand_ip = "192.168.123.211"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        
        try:
            if sock.connect((left_hand_ip, port)):
                print(f"Connected to RH56DFTP Left at {left_hand_ip}:{port}")
                self.hand_ip = left_hand_ip
            elif sock.connect((right_hand_ip, port)):
                print(f"Connected to RH56DFTP Right at {right_hand_ip}:{port}")
                self.hand_ip = right_hand_ip
        except Exception as e:
            print("Connection failed:", e)
        finally:
            sock.close()         
         
    def get_speed(self):
         
         speed = self.hand_speed

         return speed

    def set_hand(self):
         self.hand = InspireHand(ip = self.hand_ip, default_speed=self.hand_speed)

         #return hand


    #############################
    #
    #   Hand manipulation
    #
    #############################

    def move_finger(finger,angle,self):
        '''move a single finger by the given angle

             
            finger is an int value between 0 - 5, 
                relating to the finger values "Pinky", "Ring", "Middle", "Index", "Thumb bend", "Thumb rotation"
            
            angle is an int value in the renge 0 - 1000

        '''
        if not 0 <= angle <= 1000: #do nothing
            print("Error: angle not in range 0 - 1000, or not numeric. ", ValueError)
            return

        if not 0 <= finger <= 5:
            return

        self.position[finger] = angle

        self.hand.send_raw(self.position)


    def move_fingers(finger_list, angle, self):
        '''move multiple fingers to a given angle

            finger_list is a list of numerical values between 0 - 5, they represent the input of the robotic hand.
                fingers values relate to "Pinky", "Ring", "Middle", "Index", "Thumb bend", "Thumb rotation"
            
            angle is an int value in the renge 0 - 1000

            use:
            move_fingers([1,3,4],500)
    
        '''
        if not 0 <= angle <= 1000: #do nothing
                    return
        
        for finger in finger_list:
            if not 0 <= finger <= 5:
                print("Value error: ", finger, " Not identified")
                finger_list.pop(finger)
            self.position[finger] = angle

        self.hand.send_raw(self.position)
        


    def grab_object(max_force, self):
        ''' function to close hand, stopping will occur when a force reaches the max grip'''
        finger_list = [3,4]

        
    #############################
    #
    #  Read and save hand values
    #
    #############################
    
    def read_values(self):
        '''read the angle and force from the hand, '''
    
        current_forces = self.hand.read_holding(registers.FORCE_ACT, 6)
        current_angles = self.hand.read_holding(registers.ANGLE_ACT, 6)

        all_values = current_forces + current_angles

        return all_values


    def _record_loop(self):
        '''record the values every 0.25sec in the background'''

        while self._is_running:
            elapsed_time = time.time() - self._start_time

            try:
                current_data = self.read_values()
                self.sensor_table[round(elapsed_time,2)] = current_data

            except Exception as e:
                print(f"Error reading hand: {e}")

            time.sleep(0.25)

    def record_start(self):
        '''start recording the hand sensors'''
        if self._is_running:
            print("collection is already running")
            return

        self._is_running = True
        self._start_time = time.time()

        # Target the internal loop and start it on a separate background thread
        self._thread = threading.Thread(target=self._record_loop,daemon=True)
        self._thread.start()

    def record_end(self):
        '''stop recording the hand sensors'''
        if not self._is_running:
            print("Collection is not currently running")
            return

        self._is_running = False

        if self._thread:
            self._thread.join()

        return self.sensor_table

    def read_records(self):
        '''iterates through the sensor data and adds labels to the data'''
        results = {
            "Pinky":{"force":[],"angle":[]},
            "Ring":{"force":[],"angle":[]},
            "Middle":{"force":[],"angle":[]},
            "Index":{"force":[],"angle":[]},
            "Thumb bend":{"force":[],"angle":[]},
            "Thumb rotation":{"force":[],"angle":[]},
            "elapsed time":[]}

        for row in self.sensor_table:
            for finger in self.fingers:
                results[finger]["force"].append(row[0])
                results[finger]["angle"].append(row[6])
                #results={finger:{"force":[].append(row[0]),"angle":[].append(row[6])}}
                row.pop(row[0,6]) # should remove current force and angle value from results_list
        results["elapsed time"].append(self.sensor_table.keys())

        return results

    def graph_grab(self):
        data = self.read_records()

        plt.plot(data["elapsed time"], data["Index"]["force"],color ="blue") # plots the index force
        plt.plot(data["elapsed time"], data["Index"]["angle"],color ="red") # plots the index angle
        plt.plot(data["elapsed time"], data["Thumb bend"]["force"],color ="blue",linestyle = '--') # plots the Thumb bend force
        plt.plot(data["elapsed time"], data["Thumb bend"]["angle"],color ="red", linestyle ='--') # plots the thmb bend angle


    ############################
    #
    # Object Detection functions
    #
    ############################

    def object_detection(self):
        '''copy from other class, may need updating'''
        cap = cv2.VideoCapture(self.camera, cv2.CAP_DSHOW)
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
                    bbox_list = result.boxes.xyxy.tolist()          # bounding boxes all objects, you can also get xyxy with boxes.xyxy
                    clss_list = result.boxes.cls.int().tolist()     # class index all objects
                    conf_list = result.boxes.conf.tolist()          # confidence list all objects
                    for box, cls, conf in zip(bbox_list, clss_list, conf_list): #iterate over each bbox, cls and conf
                        if conf > 0.5:
                            print(f"Bounding box: {box}, Class index: {cls}, Class name:{class_names[cls]}, Confidence: {conf}")
                            #... any downstream tasks
    
    def predict_image(image,model,self):
        '''copy from other class, may need updating'''
        class_names = model.names

        prediction = model.predict(image)
        for result in prediction:
            bbox_list = result.boxes.xyxy.tolist()
            clss_list = result.boxes.cls.int().tolist()
            conf_list = result.boxes.conf.tolist()

            # theory: return  dictionary of the lists
            # data = {"location":[[x,y,w,h],[x,y,w,h]],"object_ID":[1,2],"confidence":[0.97,0.89]}
            data = {"location":bbox_list,"object_ID":clss_list,"confidence":conf_list}
        return data



    def detect_objects(self,frame):
        """
        Synchronously processes a single frame. 
        Blocks execution until inference is complete, then returns structured data.
        """
        # Run inference (stream=False forces synchronous blocking behavior)
        results = self.model(frame, verbose=False)
        
        # Access the first result object
        result = results[0]
        boxes = result.boxes
        
        detections = []
        
        for box in boxes:
            # 1. Extract location coordinates
            x, y, w, h = box.xyxy[0].tolist()
            
            # 2. Extract confidence
            confidence = float(box.conf[0])
            
            # 3. Extract object class name
            class_id = int(box.cls[0])
            object_name = self.model.names[class_id]
            
            # Build structured dictionary for this object
            detections.append({
                "object_name": object_name,
                "object_num" :class_id,
                "confidence": round(confidence, 4),
                "xyxy": [round(x, 2), round(y, 2), round(w, 2), round(h, 2)]
            })
            
        # Get the plotted image matrix directly from the result object
        annotated_frame = result.plot()
        
        # Return both the text data and the visual frame to the caller
        return detections, annotated_frame        

    ############################
    #
    # Integration
    #
    ############################
    def compare2(frame,data):
        num_items = len(data)
        if num_items <= 1:
            return
        for item in data:
            print(item)

            
        

    def compare(self,data):
            ''' compare the confidence of two readings.
                if the objects are too far away: continue
                if the objects are 
    
                TODO: 
                    Return data needs to be identified and passed
    
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
                    #print(f"Box_i: {(box_i)} \nBox_j: {(box_j)}")

                    if box_i == box_j:
                        continue

                    box_j_x1, box_j_y1, box_j_x2, box_j_y2 = box_j["xyxy"]
                   
                    box_j_mid_x = (box_j_x1 + box_j_x2)/2           
                    box_j_mid_y = (box_j_y1 + box_j_y2)/2

                    dx = abs(box_i_mid_x - box_j_mid_x)
                    dy = abs(box_i_mid_y - box_j_mid_y)
                    #print(f"dx:{dx}, dy:{dy}")

                    if dx <=2 and dy <= 2:
                        print("I dont think youre supposed to be here")#pass # they might be the same object, more testing?
                        continue
                    intersect_x1 = max(box_i_x1,box_j_x1)
                    intersect_y1 = max(box_i_y1,box_j_y1)
                    intersect_x2 = min(box_i_x2,box_j_x2)
                    intersect_y2 = min(box_i_y2,box_j_y2)

                    #print(f"x1,x2:{intersect_x1,intersect_x2}, y1,y2:{intersect_y1,intersect_y2}")
                    
                    if (intersect_x1 > intersect_x2) or (intersect_y1 > intersect_y2):
                        #print("no intersection")
                        
                        continue
                    #print("objects intersect")
                    
                    # Check whether one object is a hand
                    # and the other is an egg or ping-pong ball
                    i_is_item = box_i["object_num"] in (1, 2)
                    j_is_item = box_j["object_num"] in (1, 2)

                    i_is_hand = box_i["object_num"] == 0
                    j_is_hand = box_j["object_num"] == 0

                    if (i_is_item and j_is_hand) or (j_is_item and i_is_hand):
                        #print("charging my lazers") 

                        if i_is_hand:
                            print("huston we have liftoff")
                            pass


                        elif j_is_hand:
                            print("this has been one small step for man")
                            pass



                    

                    #if int(abs(box_i_x1 - box_j_x1)<=2) & int(abs(box_i_x2 - box_j_x1)<=2): # if they are in a range of +- 2 equal to match
                    #    print("I dont think youre supposed to be here")#pass # they might be the same object, more testing?

                    # elif int(abs(box_i["xyxy"][0] - box_j["xyxy"][0])<=40) & int(abs(box_i["xyxy"][1] - box_j["xyxy"][1])<=40):
                    #     print("charging my lasers ")
                        
                    #     if not int(abs(box_i["xyxy"][0] - box_j["xyxy"][0])<=2) & int(abs(box_i["xyxy"][1] - box_j["xyxy"][1])<=2):
                    #         #check the object class 
                    #         print("this could be it, Gary")
                    #         #if hand and egg or pingpong ball close hand 
                    #         if ((box_i["object_num"] in (1,2)) & (box_j["object_num"]== 0)) or ((box_i["object_num"]== 0) and (box_j["object_num"] in (1,2))):
                    #             # if object 1 is an egg or pingpong ball and object 2 is a hand or objects 1 and 2 is reversed...
                    #             # then pick up object
                    #             print("object will be picked up")
                    #     print("false alarm")
                    # else:
                    #     print("two objects far away")
                            
            return

    def run_main_loop(self):
        """
        Simulates your main application loop executing sequentially.
        """
        video_file = "video/raw/front_pickup_test.mov"
        cap = cv2.VideoCapture(video_file)#self.camera
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            # --- SYNCHRONOUS STEP 1: Call the object detection function ---
            # Your script will pause here until 'detect_objects' returns its values
            data, annotated_image = self.detect_objects(frame)

            # --- SYNCHRONOUS STEP 2: Run other application code sequentially ---
            # This logic safely runs knowing 'data' is fully populated
            self.process_application_logic(data)
            self.compare(data)

            # --- SYNCHRONOUS STEP 3: Display the frame ---
            cv2.imshow("Synchronous Class Pipeline", annotated_image)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

    def process_application_logic(self, data):
        """
        An example of other custom code in your class that depends on the data.
        """
        #self.compare(data)
        print(f"--- Processing Frame Data Step (Total Objects: {len(data)}) ---")
        
        for item in data:
            print(f" Found: {item['object_name']} | Match: {item['confidence']:.2%} | Location: {item['xyxy']}")

    def __main__():
        print("all the goods")
        return
    
# --- Execution ---
if __name__ == "__main__":
    # Create the class instance
    pipeline = Hand_manupultion()
    
    # Start the sequential loop
    pipeline.run_main_loop()


    ############################
    #
    # logic
    #
    ############################

    