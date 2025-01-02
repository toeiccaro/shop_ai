from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from src.api.save_img_bedding import save_user
import uvicorn
from src.services.init_singletons import init_singletons  # Import the init_singletons function

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
