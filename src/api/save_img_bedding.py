from http.client import HTTPException
import os
import base64
import time
from PIL import Image
from io import BytesIO
import psycopg2
from src.services.postgres_service import PostgresConnectionSingleton
def clean_image_folder(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

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
        if not PostgresConnectionSingleton.test_db_connection(db_instance):
            raise HTTPException(status_code=500, detail="Database connection failed")
        # Clean up the images folder before saving a new image
        directory = "tempt/images_before_save"
        if not os.path.exists(directory):
            os.makedirs(directory)
        clean_image_folder(directory)  # Clean the folder

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
        return {"error": f"Lỗi khi tính toán embedding: {e}"}

    # Lưu vào database
    try:
        # Check if the userIdPos already exists in the database
        print("before check exist")
        query_check = """
            SELECT COUNT(*) FROM users WHERE useridpos = %s::text
        """
        print("___exist")
        # db_instance.execute_query(query_check, (userIdPos,))
        # result = db_instance.fetch_one()
        # print(f"Query result: {result}")

        # print("after check exist")
        # # If the userIdPos exists, skip insertion
        # if result and result[0] > 0:
        #     return {"error": "User already exists in the database"}
        
        # If the userIdPos doesn't exist, insert new data
        query_insert = """
            INSERT INTO users (useridpos, imagepath, imgbedding)
            VALUES (%s, %s, %s)
        """
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        db_instance.get_instance().execute_query(
        """
        INSERT INTO users (useridpos, imagepath, imgbedding) 
        VALUES (%s, %s, %s)
        """,
        (None, image_path, embedding_str)
            )
        return {"message": "User saved successfully", "userIdPos": userIdPos}
    except Exception as e:
        return {"error": f"Lỗi khi lưu dữ liệu vào cơ sở dữ liệu: {e}"}
