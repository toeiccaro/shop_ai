import os
import psycopg2
from PIL import Image
from imgbeddings import imgbeddings

# 1. Kết nối tới PostgreSQL
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="shop",
        user="postgres",
        password="postgres"
    )
    print("Kết nối thành công tới PostgreSQL")
except Exception as e:
    print(f"Lỗi khi kết nối tới cơ sở dữ liệu: {e}")
    exit(1)

# 2. Khởi tạo imgbeddings
ibed = imgbeddings()

# 3. Tính embedding cho ảnh mới
new_img_path = "solo2.jpeg"
try:
    new_img = Image.open(new_img_path)
    new_embedding = ibed.to_embeddings(new_img)[0]
    print(f"Đã tính embedding cho ảnh: {new_img_path}")
except Exception as e:
    print(f"Lỗi khi xử lý ảnh {new_img_path}: {e}")
    conn.close()
    exit(1)

# 4. Truy vấn ảnh tương tự và kèm khoảng cách
cur = conn.cursor()

# Chuyển embedding sang dạng chuỗi [x1,x2,...]
embedding_str = "[" + ",".join(str(x) for x in new_embedding.tolist()) + "]"

# Lấy thêm cột 'distance' = (embedding <-> %s)
query = """
    SELECT picture,
           embedding <=> %s AS distance
    FROM pictures
    ORDER BY distance
    LIMIT 1;
"""
cur.execute(query, (embedding_str,))
rows = cur.fetchall()

# 5. Đặt ngưỡng (threshold) để quyết định "không tồn tại"
dist_threshold = 1.0  # Giá trị ví dụ, cần thử & điều chỉnh

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
