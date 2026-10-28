import cv2

def check_camera(index=0):
    # Initialize the camera object
    cap = cv2.VideoCapture(index,cv2.CAP_MSMF)
    
    # 1. Check if the camera device opened successfully
    if not cap.isOpened():
        print(f"Error: Camera at index {index} cannot be opened or is disconnected.")
        return False
        
    # 2. Double-check by attempting to read a single frame
    ret, frame = cap.read()
    if not ret or frame is None:
        print(f"Error: Camera at index {index} opened, but failed to return a frame.")
        cap.release()
        return False

    print(f"Success: Camera at index {index} is connected and working perfectly!")
    
    # Clean up and release the camera resource
    cap.release()
    return True

# Test the default webcam (index 0)
for i in range (10):
    check_camera(i)