import asyncio
import base64
from datetime import datetime
import shutil
import time
import os
import random
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
from pydantic import BaseModel
from src.api.stream_cam import check_user_exists_by_embedding
from src.api.face_detection import compute_embedding, detect_faces_and_save, read_frame_from_video
from src.api.save_img_bedding import clean_image_folder, save_user
import uvicorn
from src.services.init_singletons import init_singletons  # Import the init_singletons function
import httpx

app = FastAPI()

# Schema của yêu cầu
class SaveUserRequest(BaseModel):
    userIdPos: int | None  # userIdPos có thể là một số hoặc None
    image: str | None  # Image là base64 hoặc None
    
@app.on_event("startup")
async def startup():
    print("Initializing singletons...")
    deepface_instance, db_instance = init_singletons()  # Call init_singletons function
    app.state.deepface_instance = deepface_instance  # Store instance in app state
    app.state.db_instance = db_instance  # Store instance in app state
    print("Singletons initialized successfully")
    
@app.post("/save-user")
async def save_user_api(request: SaveUserRequest, deepface_instance=Depends(lambda: app.state.deepface_instance), db_instance=Depends(lambda: app.state.db_instance)):
    """
    API lưu người dùng vào cơ sở dữ liệu, nhận userIdPos và image (base64).
    """
    if not request.image:
        raise HTTPException(status_code=400, detail="Image is required")

    response = save_user(request.userIdPos, request.image, deepface_instance, db_instance)

    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])

    return response

def generate_mock_response():
    num_items = random.randint(4, 5)  # Random số lượng phần tử trong mảng
    mock_data = []
    
    for _ in range(num_items):
        userIdPos = random.choice([1, None])  # Randomly select between 1 and None
        image_path = "src/images/2025-01-02/1735829794.jpeg"  # Đường dẫn tới ảnh
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        
        mock_data.append({
            "userIdPos": userIdPos,
            "image": f"data:image/jpeg;base64,{encoded_image}"
        })
    
    return mock_data

# Tách phần gọi API ra thành một hàm riêng
async def call_external_api(response_item):
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "userIdPos": response_item["userIdPos"],
                "image": response_item["image"]
            }

            api_url = "https://pos.tanika.ai/api/user-info"
            api_response = await client.post(api_url, json=payload)

            # In ra kết quả từ API bên ngoài
            print(f"API response: {api_response.status_code} - {api_response.json()}")
    except Exception as e:
        print(f"Error while calling external API: {e}")

@app.post("/process-video")
async def process_video(video_path: str, deepface_instance=Depends(lambda: app.state.deepface_instance)):
    """
    API nhận video và xử lý khuôn mặt trong video.
    """
    try:
        frames = read_frame_from_video(video_path)  # Đọc các frame từ video
        result_array = []

        for frame in frames:
            try:
                print("call2")
                # Tạo thư mục tạm thời cho từng frame
                timestamp = str(int(time.time()))
                output_folder = f"tempt/images_stream/{timestamp}"
                os.makedirs(output_folder, exist_ok=True)

                # Phát hiện khuôn mặt và lưu vào thư mục
                face_paths = detect_faces_and_save(frame, output_folder)
                print("call3", face_paths)
                for face_path in face_paths:
                    print("call3.5")
                    embedding = compute_embedding(face_path)
                    print("call4")
                    if not embedding:
                        continue
                    print("call5")
                    # Chuyển ảnh thành base64
                    userIdPos = None
                    user_exists = check_user_exists_by_embedding(embedding, face_path, deepface_instance)  # Check with DB
                    if user_exists:
                        userIdPos = user_exists

                    # Chuyển ảnh thành base64
                    with open(face_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

                    result_array.append({
                        "userIdPos": userIdPos,  # Return userIdPos if found, else None
                        "Image": f"data:image/jpeg;base64,{encoded_image}"
                    })
                    print("result_array=", result_array)

                # Xóa thư mục tạm sau khi xử lý
                clean_image_folder(output_folder)
            except Exception as e:
                # Nếu có lỗi với frame này, log lỗi và tiếp tục với frame tiếp theo
                print(f"Error processing frame: {e}")
                continue  # Tiếp tục với frame tiếp theo
        print("result_array", result_array)           
        return {"result": result_array}
    
    except Exception as e:
        print(f"Error while processing video: {e}")
        raise HTTPException(status_code=500, detail="Error while processing video")

@app.post("/process-frame")
async def process_frame(payload: dict, deepface_instance=Depends(lambda: app.state.deepface_instance)):
    """
    API này nhận frame từ API 1 và xử lý khuôn mặt.
    """
    try:
        # Chuyển frame từ base64 về ảnh
        frame_data = base64.b64decode(payload["frame"])
        timestamp = str(int(time.time()))
        output_folder = f"tempt/images_stream/{timestamp}"
        os.makedirs(output_folder, exist_ok=True)

        # Đường dẫn tới file ảnh (root.jpg)
        output_image_path = os.path.join(output_folder, "root.jpg")
        with open(output_image_path, "wb") as f:
            f.write(frame_data)
        # Phát hiện khuôn mặt và lưu vào thư mục
        face_paths = detect_faces_and_save(frame_data, output_folder)

        result_array = []
        for face_path in face_paths:
            embedding = compute_embedding(face_path)
            if not embedding:
                continue
            
            print("call5")
            # Chuyển ảnh thành base64
            userIdPos = None
            user_exists = check_user_exists_by_embedding(embedding, face_path, deepface_instance)  # Check with DB
            if user_exists:
                userIdPos = user_exists
                # Chuyển ảnh thành base64
            with open(face_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                    
            result_array.append({
                "userIdPos": userIdPos,  # Return userIdPos if found, else None
                "Image": f"data:image/jpeg;base64,{encoded_image}"
            })
            print("result_array=", result_array)
        # Xóa thư mục tạm sau khi xử lý
        for response_item in result_array:
            await call_external_api(response_item)  # Gọi API ngoài để xử lý mỗi phần tử trong kết quả
        
        clean_image_folder(output_folder)

        return {"result": result_array}

    except Exception as e:
        print(f"Error while processing frame: {e}")
        raise HTTPException(status_code=500, detail="Error while processing frame")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
