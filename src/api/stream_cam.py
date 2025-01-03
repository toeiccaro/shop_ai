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

        # Convert the embedding to a format suitable for comparison (e.g., string or vector)
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        # Search for matching embeddings in the database
        query = """
            SELECT useridpos, imagepath
            FROM users
            WHERE imgbedding <-> %s::vector < 0.6  -- Assuming 0.6 as a threshold for face matching
            LIMIT 1;
        """
        cursor.execute(query, (embedding_str,))
        result = cursor.fetchone()

        if result:
            userIdPos, stored_image_path = result
            # Verify the match using DeepFace's ArcFace model
            verify_result = deepface_instance.verify_images(img1_path=image_path, img2_path=stored_image_path)
            
            # If the distance is below a threshold, it's a match
            if verify_result and verify_result < 0.6:
                return userIdPos  # Return userIdPos if the face matches
            else:
                return None
        return None
    except Exception as e:
        print(f"Error during face comparison with database: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
