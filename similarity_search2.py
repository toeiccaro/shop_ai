import os
import psycopg2
import detect.face_recognition_main as face_recognition_main
from PIL import Image

# 1. Kiểm tra khuôn mặt trong ảnh và tính embedding
new_img_path = "solo4.png"
try:
    # Load ảnh và phát hiện khuôn mặt
    image = face_recognition_main.load_image_file(new_img_path)
    face_locations = face_recognition_main.face_locations(image)

    if len(face_locations) == 0:
        print("Không phát hiện khuôn mặt trong ảnh. Dừng xử lý.")
        exit(1)

    # Tính embedding cho khuôn mặt
    encodings = face_recognition_main.face_encodings(image, face_locations)
    new_embedding = encodings[0]  # Lấy khuôn mặt đầu tiên (nếu có nhiều khuôn mặt)
    print(f"Đã tính embedding cho ảnh: {new_img_path}")

except Exception as e:
    print(f"Lỗi khi xử lý ảnh {new_img_path}: {e}")
    exit(1)

# 2. Kết nối tới PostgreSQL
try:
    conn = psycopg2.connect(
        host="db.logologee.com",
        port=5432,          # Nếu PostgreSQL chạy trên cổng mặc định
        database="shop",
        user="postgres",
        password="logologi"
    )
    print("Kết nối thành công tới PostgreSQL")
except Exception as e:
    print(f"Lỗi khi kết nối tới cơ sở dữ liệu: {e}")
    exit(1)

# 3. Truy vấn ảnh tương tự và kèm khoảng cách
cur = conn.cursor()

# Chuyển embedding sang dạng chuỗi [x1,x2,...]
embedding_str = "[" + ",".join(str(x) for x in new_embedding) + "]"

# Lấy thêm cột 'distance' = (embedding <-> %s)
query = """
    SELECT picture,
           embedding <-> %s AS distance
    FROM pictures
    ORDER BY distance
    LIMIT 1;
"""
try:
    cur.execute(query, (embedding_str,))
    rows = cur.fetchall()
except Exception as e:
    print(f"Lỗi khi truy vấn cơ sở dữ liệu: {e}")
    cur.close()
    conn.close()
    exit(1)

# 4. Đặt ngưỡng (threshold) để quyết định "không tồn tại"
dist_threshold = 0.6  # Tham số tùy chỉnh, cần thử & điều chỉnh

if rows:
    similar_filename = rows[0][0]
    distance = rows[0][1]  # Lấy giá trị distance
    similar_img_path = os.path.join("stored-faces", similar_filename)

    print(f"File giống nhất: {similar_filename}")
    print(f"Khoảng cách vector: {distance}")

    # Kiểm tra nếu lớn hơn ngưỡng => xem như "không tồn tại"
    if distance > dist_threshold:
        print(f"Không tồn tại trong cơ sở dữ liệu (distance > {dist_threshold}).")
    else:
        if os.path.isfile(similar_img_path):
            print(f"Ảnh tương tự nhất (chấp nhận): {similar_img_path}")
        else:
            print(f"Không tìm thấy file trên disk: {similar_img_path}")
else:
    print("Không tìm thấy ảnh tương tự trong cơ sở dữ liệu.")

# Đóng cursor & kết nối
cur.close()
conn.close()
print("Đã đóng kết nối tới cơ sở dữ liệu.")
