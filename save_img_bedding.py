import os
from deepface import DeepFace
import psycopg2
import tensorflow as tf

print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
print("Details:", tf.config.list_physical_devices('GPU'))

# Kết nối tới cơ sở dữ liệu PostgreSQL
try:
    conn = psycopg2.connect(
        host="db.logologee.com",
        port=5555,
        database="shop01",
        user="postgres",
        password="logologi"
    )
    print("Kết nối thành công tới PostgreSQL")
except Exception as e:
    print(f"Lỗi khi kết nối tới cơ sở dữ liệu: {e}")
    exit(1)

# Tạo đối tượng cursor
cur = conn.cursor()

# Duyệt qua các file ảnh trong thư mục stored-faces
folder_path = "stored-faces"
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    if os.path.isfile(file_path):
        try:
            # Kiểm tra xem imagepath đã tồn tại hay chưa
            cur.execute("SELECT COUNT(*) FROM users WHERE imagepath = %s", (filename,))
            count = cur.fetchone()[0]

            if count > 0:
                print(f"Ảnh {filename} đã tồn tại trong cơ sở dữ liệu. Bỏ qua.")
                continue  # Bỏ qua nếu ảnh đã tồn tại

            # Tính toán embedding bằng ArcFace
            result = DeepFace.represent(img_path=file_path, model_name="ArcFace", enforce_detection=True)
            embedding = result[0]["embedding"]

            # Chèn dữ liệu vào bảng users
            cur.execute(
                """
                INSERT INTO users (useridpos, imagepath, imgbedding) 
                VALUES (%s, %s, %s)
                """,
                (None, filename, embedding)
            )

            print(f"Đã ghi embedding cho file: {filename}")
        except ValueError as ve:
            # Bỏ qua ảnh không có khuôn mặt
            print(f"Bỏ qua file {filename}: Không phát hiện được khuôn mặt.")
            continue
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh {filename}: {e}")
            conn.rollback()  # Rollback giao dịch nếu có lỗi
            continue          # Tiếp tục với ảnh tiếp theo

# Lưu thay đổi
conn.commit()

# Đóng kết nối
cur.close()
conn.close()
print("Đã đóng kết nối tới cơ sở dữ liệu")
