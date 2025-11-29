from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(
    prefix="/search",
    tags=["Search (검색)"],
)

# ==========================================
# [API 28] 유저 검색 (닉네임 일부만 맞아도 나옴)
# ==========================================
@router.get("/users", response_model=list[schemas.UserResponse])
def search_users(keyword: str, db: Session = Depends(get_db)):
    # LIKE %keyword% 검색
    return db.query(models.User).filter(models.User.nickname.like(f"%{keyword}%")).all()

# ==========================================
# [API 29] 게시글 내용 검색
# ==========================================
@router.get("/posts", response_model=list[schemas.PostResponse])
def search_posts(keyword: str, db: Session = Depends(get_db)):
    return db.query(models.Post).filter(models.Post.content.like(f"%{keyword}%")).all()

# ==========================================
# [API - 추가] 아이디(이메일)로 유저 검색
# ==========================================
@router.get("/users/id", response_model=list[schemas.UserResponse])
def search_users_by_email(keyword: str, db: Session = Depends(get_db)):
    # 이메일에 검색어가 포함된 유저를 찾는다. (예: "test" -> test@naver.com 검색됨)
    return db.query(models.User).filter(models.User.email.like(f"%{keyword}%")).all()