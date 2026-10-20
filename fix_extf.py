import os
from os import listdir
from PIL import Image, ExifTags
'''
the puropose of this code is to 

Code retrieved from:
https://stackoverflow.com/questions/13872331/rotating-an-image-with-orientation-specified-in-exif-using-python-without-pil-in
https://www.geeksforgeeks.org/python/how-to-iterate-through-images-in-a-folder-python/

'''


def fix_image(filepath):
    try:
        image=Image.open(filepath)

        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
    
        exif = image._getexif()

        if exif == None:
            print(f'object not subscriptable: {image}')
            pass
        elif exif[orientation] == 3:
            image=image.rotate(180, expand=True)
            print("180 deg")
        elif exif[orientation] == 6:
            image=image.rotate(270, expand=True)
            print("270 deg")
        elif exif[orientation] == 8:
            image=image.rotate(90, expand=True)
            print("90 deg")
        else:
            print("no change")

        image.save(filepath)
        image.close()
    except (AttributeError, KeyError, IndexError):
        # cases: image don't have getexif
        print("no extf")
        pass


def main():

    # get the path or directory
    folder_dir = input("Enter the File Directory:")  #"C:/Users/kylee/OneDrive/Documents/USC/ICT 342/Hand py/image_extf_fix/New Folder/test/images"
    for images in os.listdir(folder_dir):

        # check if the image ends with png or jpg or jpeg
        if (images.endswith(".png") or images.endswith(".jpg")\
            or images.endswith(".jpeg")):
            # display
            path =(folder_dir+ "/" + images)
            print(path)
            fix_image(path)

main()