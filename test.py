from deepface import DeepFace

try:
    result = DeepFace.analyze(img_path="solo4.png", actions=["gender"])
    print(result)
except Exception as e:
    print(f"Lỗi khi xử lý DeepFace: {e}")