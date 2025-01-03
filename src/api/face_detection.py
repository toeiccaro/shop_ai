import base64
import os
import time
import shutil
import cv2
from io import BytesIO
from PIL import Image
import numpy as np
from retinaface import RetinaFace
from deepface import DeepFace

haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# 1. Hàm đọc ảnh từ video và cắt mỗi 3 giây
def read_frame_from_video(video_path):
    cap = cv2.VideoCapture(video_path)  # Make sure the correct URL is passed here
    if not cap.isOpened():  # Check if the stream was successfully opened
        print("Error: Couldn't open video stream.")
        return []

    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))  # Get the frame rate from the stream
    frames = []
    print("frame_rate", frame_rate)
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # print("frame")
        # Chỉ lấy ảnh mỗi 3 giây
        if frame_count % (3 * frame_rate) == 0:
            # Chuyển frame thành ảnh (buffer)
            _, buffer = cv2.imencode('.jpg', frame)
            img_buffer = buffer.tobytes()
            frames.append(img_buffer)
        # print("frame_count", frame_count)
        frame_count += 1

    cap.release()
    return frames

# 2. Dọn dẹp thư mục lưu ảnh
def clean_image_folder(directory):
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)  # Xóa thư mục và tất cả các tệp bên trong
            print(f"Đã xóa thư mục: {directory}")
    except Exception as e:
        print(f"Failed to delete folder: {e}")

# 3. Chuyển đổi ảnh từ buffer thành base64
def convert_image_to_base64(img_buffer):
    img = Image.open(BytesIO(img_buffer))
    with BytesIO() as output:
        img.save(output, format="JPEG")
        encoded_image = base64.b64encode(output.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded_image}"

# 4. Hàm nhận diện và lưu khuôn mặt
def detect_faces_and_save(input_image_buffer, output_folder):
    # Open the image from the buffer
    img = Image.open(BytesIO(input_image_buffer))
    print("call3.1")
    
    # Convert image to grayscale as Haar Cascade works on grayscale images
    gray_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    
    # Detect faces in the grayscale image
    faces = haar_cascade.detectMultiScale(
        gray_img, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
    )
    
    print("call3.2")
    
    face_paths = []
    counter = 0
    
    # Process each face detected
    for (x, y, w, h) in faces:
        print("call3.4")
        # Crop the image to select only the face
        cropped_face = img.crop((x, y, x + w, y + h))
        
        # Generate a unique file name using timestamp and counter
        timestamp = int(time.time() * 1000)
        unique_id = timestamp + counter
        output_file_path = os.path.join(output_folder, f"{unique_id}.jpg")
        
        # Save the cropped face to the output folder
        cropped_face.save(output_file_path)
        face_paths.append(output_file_path)
        counter += 1

    return face_paths

# 5. Hàm tính toán embedding từ ảnh
def compute_embedding(image_path):
    try:
        result = DeepFace.represent(img_path=image_path, model_name="ArcFace", enforce_detection=True)
        return result[0]["embedding"]
    except Exception as e:
        print(f"Error when processing {image_path}: {e}")
        return None
