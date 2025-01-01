import os
import psycopg2
from deepface import DeepFace

# 1. Tính toán embedding cho ảnh mới bằng ArcFace
new_img_path = "image_from_goc_2.jpg"
try:
    result = DeepFace.represent(img_path=new_img_path, model_name="ArcFace", enforce_detection=True)
    new_embedding = result[0]["embedding"]
    print(f"Đã tính embedding cho ảnh: {new_img_path}")
except Exception as e:
    print(f"Lỗi khi xử lý ảnh {new_img_path}: {e}")
    exit(1)

# 2. Kết nối tới PostgreSQL
try:
    conn = psycopg2.connect(
        host="db.logologee.com",
        port=5555,  # Nếu PostgreSQL chạy trên cổng mặc định
        database="shop01",
        user="postgres",
        password="logologi"
    )
    print("Kết nối thành công tới PostgreSQL")
    cur = conn.cursor()
except Exception as e:
    print(f"Lỗi khi kết nối tới cơ sở dữ liệu: {e}")
    exit(1)

# 3. Truy vấn 5 ảnh có khoảng cách nhỏ nhất
query = """
    SELECT imagepath,
           imgbedding <-> %s::vector AS distance
    FROM users
    ORDER BY distance
    LIMIT 5;
"""
embedding_str = "[" + ",".join(str(x) for x in new_embedding) + "]"
try:
    cur.execute(query, (embedding_str,))
    rows = cur.fetchall()
except Exception as e:
    print(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}")
    cur.close()
    conn.close()
    exit(1)

# 4. Xác minh bằng ArcFace
threshold = 0.6  # Ngưỡng khoảng cách để xác định là "giống nhau"
for row in rows:
    stored_image_path = row[0]  # Đường dẫn ảnh trong cơ sở dữ liệu
    print(f"Đang xác minh với ảnh: {stored_image_path}")

    try:
        # Sử dụng DeepFace để xác minh
        verify_result = DeepFace.verify(img1_path=new_img_path, img2_path=os.path.join("stored-faces", stored_image_path), model_name="ArcFace")
        distance = verify_result['distance']
        print(f"Khoảng cách so sánh: {distance}")

        if distance < threshold:
            print(f"Ảnh {stored_image_path} được xác minh là giống với khoảng cách {distance}")
            # Đóng kết nối trước khi return
            cur.close()
            conn.close()
            print("Đã đóng kết nối tới cơ sở dữ liệu.")
            exit(True)
    except Exception as e:
        print(f"Lỗi khi xác minh với ảnh {stored_image_path}: {e}")

# Nếu không có ảnh nào giống
print("Không tìm thấy ảnh nào giống trong cơ sở dữ liệu.")
# Đóng cursor & kết nối
cur.close()
conn.close()
print("Đã đóng kết nối tới cơ sở dữ liệu.")
exit(False)
