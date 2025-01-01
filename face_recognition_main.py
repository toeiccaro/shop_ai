import os
import cv2
import time
from retinaface import RetinaFace

# Đường dẫn đến ảnh cần xử lý
input_image_path = "image_goc_2.png"

# Đọc ảnh
image = cv2.imread(input_image_path)
if image is None:
    print(f"Không thể đọc ảnh từ đường dẫn: {input_image_path}")
    exit(1)

# Phát hiện khuôn mặt bằng RetinaFace
faces = RetinaFace.detect_faces(input_image_path)

# Đảm bảo thư mục lưu khuôn mặt đã tồn tại
output_folder = 'stored-faces'
os.makedirs(output_folder, exist_ok=True)

# Xử lý từng khuôn mặt được phát hiện
counter = 0  # Counter để tạo tên file duy nhất
for key, face in faces.items():
    try:
        # Lấy tọa độ bounding box của khuôn mặt
        facial_area = face['facial_area']  # [x1, y1, x2, y2]
        x1, y1, x2, y2 = facial_area

        # Crop khuôn mặt từ ảnh gốc
        cropped_face = image[y1:y2, x1:x2]

        # Tạo tên file duy nhất bằng timestamp và counter
        timestamp = int(time.time() * 1000)  # Milliseconds since epoch
        unique_id = timestamp + counter  # Kết hợp timestamp và counter
        output_file_path = os.path.join(output_folder, f"{unique_id}.jpg")

        # Lưu khuôn mặt đã crop vào file
        cv2.imwrite(output_file_path, cropped_face)

        print(f"Đã lưu khuôn mặt vào: {output_file_path}")

        # Tăng counter để đảm bảo tính duy nhất
        counter += 1
    except Exception as e:
        print(f"Lỗi khi xử lý khuôn mặt: {e}")

print("Hoàn thành việc phát hiện và cắt khuôn mặt.")
