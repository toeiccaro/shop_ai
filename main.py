import asyncio
import base64
from datetime import time
import os
import random
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
from pydantic import BaseModel
from src.api.save_img_bedding import save_user
import uvicorn
from src.services.init_singletons import init_singletons  # Import the init_singletons function
from src.api.stream_cam import process_and_compare_faces
import cv2
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
    # Randomly choose userIdPos to be 1 or None
    userIdPos = random.choice([1, None])  # Randomly select between 1 and None
    
    image_path = "src/images/2025-01-02/1735829794.jpeg"  # Đường dẫn tới ảnh
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    response = {
        "userIdPos": str(userIdPos),
        "image": f"data:image/jpeg;base64,{encoded_image}"
    }
    return response

@app.post("/stream-cam")
async def stream_cam(background_tasks: BackgroundTasks):
    """
    API trả về response mock mỗi 5 giây và gửi request tới API bên ngoài.
    """
    async def process_and_return_response():
        while True:
            response = generate_mock_response()
            print("Generated mock response:", response)  # Log ra terminal

            # Gửi POST request tới API https://pos.tanika.ai/api/user-info
            async with httpx.AsyncClient() as client:
                try:
                    payload = {
                        "userIdPos": response["userIdPos"],
                        "image": response["image"]
                    }

                    api_url = "https://pos.tanika.ai/api/user-info"
                    api_response = await client.post(api_url, json=payload)

                    # In ra kết quả từ API bên ngoài
                    print(f"API response: {api_response.status_code} - {api_response.json()}")

                except Exception as e:
                    print(f"Error while calling external API: {e}")

            await asyncio.sleep(5)  # Chờ 5 giây trước khi gửi lại

    # Chạy task bất đồng bộ trong nền
    background_tasks.add_task(process_and_return_response)
    return {"message": "Started processing camera stream"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
