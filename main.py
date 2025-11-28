from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import engine
import models
from routers import users, posts, comments # <--- [1] comments 추가

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="인스타그램 API", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router) # <--- [2] 등록 추가

@app.get("/")
def read_root():
    return {"message": "인스타그램 서버 정상 작동 중!"}