import os
import numpy as np
from imgbeddings import imgbeddings
from PIL import Image
import psycopg2

# Kết nối tới cơ sở dữ liệu PostgreSQL
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,          # Nếu PostgreSQL chạy trên cổng mặc định
        database="shop",
        user="postgres",
        password="postgres"
    )
    print("Kết nối thành công tới PostgreSQL")
except Exception as e:
    print(f"Lỗi khi kết nối tới cơ sở dữ liệu: {e}")
    exit(1)

# Tạo đối tượng cursor
cur = conn.cursor()

# Khởi tạo imgbeddings để tính toán embedding
ibed = imgbeddings()

# Duyệt qua các file ảnh trong thư mục stored-faces
folder_path = "stored-faces"
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # Chỉ xử lý nếu là file (tránh xử lý folder khác)
    if os.path.isfile(file_path):
        try:
            # Đọc ảnh
            img = Image.open(file_path)

            # Tính toán embedding
            embedding = ibed.to_embeddings(img)[0]  # ibed.to_embeddings() trả về mảng, lấy phần tử đầu

            # Chèn dữ liệu vào bảng pictures
            cur.execute(
                "INSERT INTO pictures (picture, embedding) VALUES (%s, %s)",
                (filename, embedding.tolist())
            )

            print(f"Đã ghi embedding cho file: {filename}")
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh {filename}: {e}")

# Lưu thay đổi
conn.commit()

# Đóng kết nối
cur.close()
conn.close()
print("Đã đóng kết nối tới cơ sở dữ liệu")
