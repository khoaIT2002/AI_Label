from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, status
from routers.users import router as user_router 
from routers.roles import router as role_router
from routers.projects import router as project_router
from routers.ai_models import router as ai_model



app = FastAPI(

    title="Fast API Label Automation System",
    description="Label AI for managing traffic camera.",
    version="0.0.1",
    contact={
        "name": "Khoa_BEWY",
        "email": "anhkhoa01010902.atg@example.com",
    },
    license_info={
        "name": "BKU",
    },
)


origins = [
    "http://localhost:3000",  # Nguồn gốc của React app
    # Thêm các nguồn gốc khác nếu cần
]

app.add_middleware(
      CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"], 
  


    
)
@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(user_router, prefix="/users", tags=["users"])
app.include_router(role_router, tags=["roles"])
app.include_router(project_router, prefix="/projects", tags=["projects"])
app.include_router(ai_model, prefix="/ai_models", tags=["ai_models"])
# Redirect to docs
