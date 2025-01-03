from datetime import datetime
import os
import base64
import time
from PIL import Image
from io import BytesIO
import psycopg2
import shutil

# Kết nối đến cơ sở dữ liệu PostgreSQL
conn = psycopg2.connect(
    host="db.logologee.com",
    port=5555,
    database="shop01",
    user="postgres",
    password="logologi"
)
print("Kết nối thành công tới PostgreSQL")

# Hàm để dọn dẹp thư mục hình ảnh
def clean_image_folder(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            shutil.rmtree(directory)
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

# Hàm chuyển đổi base64 thành ảnh
def save_base64_as_image(base64_string):
    try:
        # Remove the data URI prefix if it exists
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
        
        # Decode the base64 string into bytes
        img_data = base64.b64decode(base64_string)
        
        # Check if the image data is valid
        if len(img_data) == 0:
            raise ValueError("Decoded image data is empty")
        
        # Convert bytes to a PIL Image object
        img = Image.open(BytesIO(img_data))
        return img
    except Exception as e:
        print(f"Error: {e}")
        return None

# Lưu ảnh và embedding vào cơ sở dữ liệu
def save_user(userIdPos, image_base64, deepface_instance, db_instance):
 
    try:
        print("before check exist")
        query_check = "SELECT COUNT(*) FROM users WHERE useridpos = %s"
        print(f"Executing query: {query_check} with params: ({str(userIdPos)},)")

        with conn.cursor() as cur:  # Use context manager for cursor
            cur.execute(query_check, (str(userIdPos),))  # Chuyển đổi userIdPos thành chuỗi
            result = cur.fetchone()
        
        if result:
            count = result[0]
            print(f"Query-result: {count}")
        else:
            print("No result returned.")
            count = 0

        # Nếu userIdPos đã tồn tại, bỏ qua
        if count > 0:
            print(f"Ảnh đã tồn tại trong cơ sở dữ liệu. Bỏ qua.")
            return {"message": "User already exists in the database"}  # Bỏ qua nếu ảnh đã tồn tại    
    except Exception as e:
            return {"error": f"Error when check exist: {e}"}
    try:
        # Clean up the images folder before saving a new image
        today = datetime.today().strftime('%Y-%m-%d')  # Get today's date in YYYY-MM-DD format
        directory = os.path.join("src/images", today)  # Path with today's date

        if not os.path.exists(directory):
            os.makedirs(directory)  # Create the directory if it doesn't exist

        # Save the base64 image as a PIL Image object
        img = save_base64_as_image(image_base64)
        if not img:
            return {"error": "Failed to save image"}

        # Get timestamp for filename
        timestamp = str(int(time.time()))  # Current Unix timestamp
        image_format = img.format.lower()  # Get image format (e.g., 'jpeg', 'png')
        image_path = os.path.join(directory, f"{timestamp}.{image_format}")
        
        # Save the image to the folder
        try:
            img.save(image_path, format=img.format)  # Save image in its original format
        except Exception as e:
            return {"error": f"Failed to save image: {e}"}

    except Exception as e:
        return {"error": f"Lỗi khi giải mã base64 hoặc lưu ảnh: {e}"}
    
    # Tính toán embedding
    try:
        embedding = deepface_instance.compute_embedding(image_path)
        print("embedding", embedding)
        if not embedding:
            return {"error": "Failed to process image"}
    except Exception as e:
        print(f"Error during embedding calculation: {e}")
        return {"error": f"Lỗi khi tính toán embedding: {e}"}

    # Kiểm tra nếu userIdPos đã tồn tại trong cơ sở dữ liệu

    try:
        # Nếu userIdPos không tồn tại, thêm mới vào cơ sở dữ liệu
        query_insert = """
            INSERT INTO users (useridpos, imagepath, imgbedding)
            VALUES (%s, %s, %s)
        """
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        with conn.cursor() as cur:  # Use context manager for cursor
            cur.execute(query_insert, (str(userIdPos), image_path, embedding_str))  # Chuyển đổi userIdPos thành chuỗi
            conn.commit()  # Đảm bảo commit để lưu thay đổi vào cơ sở dữ liệu
            print(f"Đã ghi embedding cho ảnh: {image_path}")
        
        return {"message": "User saved successfully", "userIdPos": userIdPos}
    
    except Exception as e:
        print(f"Error while saving data: {e}")
        return {"error": f"Lỗi khi lưu dữ liệu vào cơ sở dữ liệu: {e}"}
