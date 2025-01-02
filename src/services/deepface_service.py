from deepface import DeepFace

class DeepFaceSingleton:
    _instance = None

    @staticmethod
    def get_instance():
        if DeepFaceSingleton._instance is None:
            DeepFaceSingleton._instance = DeepFaceSingleton()
        return DeepFaceSingleton._instance

    def compute_embedding(self, img_path):
        try:
            result = DeepFace.represent(img_path=img_path, model_name="ArcFace", enforce_detection=True)
            embedding = result[0]["embedding"]
            print(f"Đã tính embedding cho ảnh: {img_path}")
            return embedding
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh {img_path}: {e}")
            return None

    def verify_images(self, img1_path, img2_path):
        try:
            verify_result = DeepFace.verify(img1_path=img1_path, img2_path=img2_path, model_name="ArcFace")
            distance = verify_result['distance']
            print(f"Khoảng cách so sánh: {distance}")
            return distance
        except Exception as e:
            print(f"Lỗi khi xác minh với ảnh {img2_path}: {e}")
            return None
