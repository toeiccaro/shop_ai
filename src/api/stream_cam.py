import os
import base64
import time
from PIL import Image
from io import BytesIO
import cv2
import psycopg2
from deepface import DeepFace
from retinaface import RetinaFace
import shutil

# 1. Hàm kết nối với PostgreSQL
def connect_to_db():
    try:
        conn = psycopg2.connect(
            host="db.logologee.com",
            port=5555,
            database="shop01",
            user="postgres",
            password="logologi"
        )
        print("Kết nối thành công tới PostgreSQL")
        return conn
    except Exception as e:
        print(f"Lỗi khi kết nối tới cơ sở dữ liệu: {e}")
        exit(1)

# 2. Hàm dọn dẹp thư mục lưu ảnh
def clean_image_folder(directory):
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)  # Xóa thư mục và tất cả các tệp bên trong
            print(f"Đã xóa thư mục: {directory}")
    except Exception as e:
        print(f"Failed to delete folder: {e}")

# 3. Hàm chuyển đổi base64 thành ảnh
def save_base64_as_image(base64_string):
    try:
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        img_data = base64.b64decode(base64_string)
        if len(img_data) == 0:
            raise ValueError("Decoded image data is empty")
        
        img = Image.open(BytesIO(img_data))
        return img
    except Exception as e:
        print(f"Error: {e}")
        return None

# 4. Hàm nhận diện và lưu khuôn mặt
def detect_faces_and_save(input_image_path, output_folder):
    image = cv2.imread(input_image_path)
    if image is None:
        print(f"Không thể đọc ảnh từ đường dẫn: {input_image_path}")
        return []
    
    faces = RetinaFace.detect_faces(input_image_path)
    os.makedirs(output_folder, exist_ok=True)

    face_paths = []
    counter = 0
    for key, face in faces.items():
        try:
            facial_area = face['facial_area']
            x1, y1, x2, y2 = facial_area
            cropped_face = image[y1:y2, x1:x2]
            
            timestamp = int(time.time() * 1000)
            unique_id = timestamp + counter
            output_file_path = os.path.join(output_folder, f"{unique_id}.jpg")
            cv2.imwrite(output_file_path, cropped_face)
            face_paths.append(output_file_path)
            counter += 1
        except Exception as e:
            print(f"Lỗi khi xử lý khuôn mặt: {e}")

    return face_paths

# 5. Hàm tính toán embedding từ ảnh
def compute_embedding(image_path):
    try:
        result = DeepFace.represent(img_path=image_path, model_name="ArcFace", enforce_detection=True)
        return result[0]["embedding"]
    except Exception as e:
        print(f"Lỗi khi xử lý ảnh {image_path}: {e}")
        return None

# 6. Hàm kiểm tra xem người dùng đã tồn tại trong DB hay chưa
def check_user_exists(userIdPos, db_instance):
    try:
        query_check = "SELECT COUNT(*) FROM users WHERE useridpos = %s"
        db_instance.execute_query(query_check, (str(userIdPos),))
        result = db_instance.fetch_one()
        
        if result:
            count = result[0]
            return count > 0
        return False
    except Exception as e:
        print(f"Error during checking user existence: {e}")
        return False

# 7. Hàm tìm kiếm ảnh tương tự trong cơ sở dữ liệu
def similarity_search(image_path, db_instance):
    embedding = compute_embedding(image_path)
    if not embedding:
        return {"error": "Failed to compute embedding"}
    
    try:
        query = """
            SELECT imagepath, imgbedding <-> %s::vector AS distance
            FROM users
            ORDER BY distance
            LIMIT 5;
        """
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        db_instance.execute_query(query, (embedding_str,))
        rows = db_instance.fetch_all()
        
        threshold = 0.6
        similar_images = []
        for row in rows:
            stored_image_path = row[0]
            verify_result = DeepFace.verify(img1_path=image_path, img2_path=os.path.join("stored-faces", stored_image_path), model_name="ArcFace")
            distance = verify_result['distance']
            if distance < threshold:
                similar_images.append(stored_image_path)
        return similar_images
    
    except Exception as e:
        print(f"Error while searching for similar images: {e}")
        return {"error": f"Lỗi khi tìm kiếm ảnh tương tự: {e}"}

# 8. Hàm chính để xử lý ảnh và so sánh
def process_and_compare_faces(userIdPos, image_base64, input_image_path, db_instance):
    timestamp = str(int(time.time()))
    output_folder = f"stored-faces-{timestamp}"  # Tạo thư mục mới dựa trên timestamp
    face_paths = detect_faces_and_save(input_image_path, output_folder)
    if not face_paths:
        return {"error": "No faces detected"}
    
    result_array = []
    for face_path in face_paths:
        embedding = compute_embedding(face_path)
        if not embedding:
            return {"error": "Failed to compute embedding for the face"}
        
        user_exists = check_user_exists(userIdPos, db_instance)
        userId = userIdPos if user_exists else None

        # Chuyển ảnh đã cắt thành base64
        with open(face_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        result_array.append({
            "userIdPos": userId,
            "Image": f"data:image/jpeg;base64,{encoded_image}"
        })
    
    # Xóa thư mục và ảnh sau khi hoàn tất xử lý
    clean_image_folder(output_folder)
    
    return result_array
