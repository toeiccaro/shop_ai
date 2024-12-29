import os
# import the OpenCV library - it's called cv2
import cv2

# load the Haar Cascade algorithm from the XML file into OpenCV
haar_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# read the test image as grayscale
gray_img = cv2.imread("test-image.png", cv2.IMREAD_GRAYSCALE)

# find the faces in that image
# this gives back an array of the x,y location of each face, and its width and height
faces = haar_cascade.detectMultiScale(
    gray_img, scaleFactor=1.05, minNeighbors=2, minSize=(100, 100)
)

# make sure the directory we're going to write to actually exists
os.makedirs('stored-faces', exist_ok=True)

i = 0
# write all the faces out to files
# for each face we found:
for x, y, w, h in faces:
    # crop the image to select only the face
    cropped_image = gray_img[y : y + h, x : x + w]
    # make up a filename for that face - we're just going to number them
    target_file_name = f'stored-faces/{i}.jpg'
    # report each file so we can tell we're doing something
    print(target_file_name)
    # and write the cropped face to the file
    cv2.imwrite(
        target_file_name,
        cropped_image,
    )
    i = i + 1