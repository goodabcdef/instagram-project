from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies
import shutil
import os

router = APIRouter(
    prefix="/posts", # 이 파일의 모든 API는 앞에 /posts가 붙음
    tags=["Post (게시글)"],
)

# 사진 저장할 폴더 만들기
UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# [API 4] 게시글 작성 (사진 업로드 포함)
# ==========================================
@router.post("", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    content: str = Form(...),                    # 내용 (Form 데이터로 받음)
    file: UploadFile = File(...),                # 사진 파일
    current_user: models.User = Depends(dependencies.get_current_user), # 로그인한 사람만
    db: Session = Depends(get_db)
):
    # 1. 파일 이름 겹치지 않게 변경 (유저ID_시간_원래이름)
    filename = f"{current_user.id}_{file.filename}"
    file_path = f"{UPLOAD_DIR}/{filename}"
    
    # 2. 서버 컴퓨터에 사진 저장 (static/images 폴더에)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. DB에 게시글 정보 저장
    # (이미지 주소는 웹에서 접속 가능한 URL 형태로 저장)
    db_post = models.Post(
        content=content,
        image_url=f"/static/images/{filename}",
        user_id=current_user.id
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

# ==========================================
# [API 5] 게시글 전체 조회 (최신순)
# ==========================================
@router.get("", response_model=list[schemas.PostResponse])
def read_posts(db: Session = Depends(get_db)):
    # 내림차순(desc) 정렬해서 가져오기
    return db.query(models.Post).order_by(models.Post.created_at.desc()).all()

# ==========================================
# [API 17] 특정 유저가 쓴 글 모아보기 (프로필용)
# ==========================================
@router.get("/user/{user_id}", response_model=list[schemas.PostResponse])
def read_user_posts(user_id: int, db: Session = Depends(get_db)):
    posts = db.query(models.Post).filter(models.Post.user_id == user_id).order_by(models.Post.created_at.desc()).all()
    return posts

# ==========================================
# [API 18] 게시글 상세 조회 (1개만 보기)
# ==========================================
@router.get("/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post

# ==========================================
# [API 19] 게시글 수정 (내용만)
# ==========================================
@router.put("/{post_id}", response_model=schemas.PostResponse)
def update_post(
    post_id: int,
    post_update: schemas.PostUpdate,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")
    
    # 작성자 본인 확인 (관리자는 프리패스)
    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

    post.content = post_update.content
    db.commit()
    db.refresh(post)
    return post

# ==========================================
# [API 20] 게시글 삭제
# ==========================================
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")

    # 작성자 본인 확인
    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    
    db.delete(post)
    db.commit()
    return