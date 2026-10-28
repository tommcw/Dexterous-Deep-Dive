import cv2
from ultralytics import YOLO

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("DirectShow failed to open camera.")
else:
    model = YOLO("yolo11n.pt")
    predictions =model.predict(source= 0, show =True)

    while True:
        ret, frame = cap.read()
        #model = YOLO("weights.pt")

        if not ret:
            ("fail")
            break

        # Send frame to inference
        #predictions = model.predict(frame)

        for result in predictions:

            # Get detected bounding boxes
            boxes = result.boxes

            for box in boxes:

                # Class ID
                class_id = int(box.cls[0])

                # Class name
                object_name = model.names[class_id]

                # Confidence
                confidence = float(box.conf[0])

                # Bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                print(
                    object_name,
                    confidence,
                    x1,
                    y1,
                    x2,
                    y2
                )

        # Display camera
        #cv2.imshow("YOLO Detection", frame)

        # ESC to quit
        if cv2.waitKey(1) == 27:
            break

    cap.release()
