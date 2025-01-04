import psycopg2
from datetime import datetime

def check_user_exists_by_embedding(embedding, image_path, deepface_instance):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="db.logologee.com",
            port=5555,
            database="shop01",
            user="postgres",
            password="logologi"
        )
        cursor = conn.cursor()
        print("call5.1")
        # Chuyển đổi embedding thành chuỗi để so sánh
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        print("embedding_strembedding_str=", embedding_str)

        # Tìm kiếm các embeddings trong cơ sở dữ liệu với khoảng cách nhỏ hơn ngưỡng 0.6
        query = """
            SELECT userIdPos, imagepath,
                   imgbedding <-> %s::vector AS distance
            FROM users
            ORDER BY distance
            LIMIT 5;
        """
        print("call5.2")
        cursor.execute(query, (embedding_str, ))
        print("call5.3")
        rows = cursor.fetchall()
        print("rowsrowsrows=", rows)
        if rows:
            for row in rows:
                userIdPos, imagepath, distance = row
                print(f"Phát hiện userIdPos: {userIdPos}, imagepath: {imagepath}")
                print("image_pathimage_path1=", image_path)
                print("image_pathimage_path2=", imagepath)

                # Sử dụng DeepFace để xác minh khuôn mặt
                verify_result = deepface_instance.verify_images(img1_path=image_path, img2_path=imagepath)
                print("verify_resultverify_result=", verify_result)
                # Nếu khoảng cách nhỏ hơn ngưỡng 0.6, là trùng khớp
                if verify_result and verify_result['distance'] < 0.6:
                    print(f"Xác minh thành công: Ảnh {imagepath} trùng khớp với khoảng cách {verify_result['distance']}")
                    return userIdPos  # Trả về userIdPos nếu khuôn mặt trùng khớp
                else:
                    print(f"Xác minh thất bại: Khoảng cách {verify_result['distance']} vượt quá ngưỡng")

            return None
        else:
            print("Không tìm thấy userIdPos tương ứng với embedding trong cơ sở dữ liệu.")
            return None
    except Exception as e:
        print(f"Lỗi khi so sánh khuôn mặt với cơ sở dữ liệu: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
