Authors:
    Kyle Griffin 1137837
    Thomas McWaters 1177282
 
Last Updated: 
    28/10/26 21:45 AEST

The application for the replacement user interface can be found in the ui_subproject folder.
To launch the application run the hand_control.py script.

The proof_of_work folder contains proof of work on the assignment this includes:

    hand_Communication_serial : 
        records of attempts at serial communication with the robotic hand.
        Each successive attempt shows how we were able to troubleshoot and move closer 
        towards successful communication.

    hand_manipulation : 
        files associated with manipulation of the robotic hand.

    Object_detection : 
        files associated with running the object detection model locally.

The videos folder contains the raw files and evaluated videos named after the model 
created using video_eval3.py.

The Object_Detection_Folder_models contains the weights of object detection models trained
using roboflow. their names have been updated to interpret the model, some model names not 
included are present in the files, this is due to the renaming and may cause some bugs when running.

The Hand_and_objects_dataset.yolov11 contains the images and annotations used 
in training the object detection model.

fix_exif.py contains the work around for the rotating images bug.
by running the fix_exif.py script, the user will be prompted to provide a file location. this
must be relative to the script or be the full path. images will be iterated through and altered if
there is the relevant metadata attached.

video_eval3.py can be used to add model predictions and bounding boxes 
to a video file using the model.
by running the video_eval3.py script, the user will be prompted to provide a model and video file,
it will inform on the location that the file needs to be in those locations.

hand_manipulation.py is the implementation of the integration between hand 
and model for object dependent manipulation.
This script is not complete. 

recording_logic_test.py is the the logic test developed towards full intergration. 
It is able to take a video and identify when two objects intersect. 

