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
async def create_post(  # async 붙여주세요 (파일 읽기 위해)
    content: str = Form(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    # [추가 1] 415 에러: 이미지 파일이 아니면 거절
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="이미지 파일(jpg, png 등)만 업로드 가능합니다."
        )

    # [추가 2] 413 에러: 파일 크기가 5MB 넘으면 거절
    # (파일을 살짝 읽어서 크기 확인)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0) # 다시 처음으로 돌려놓기
    
    if file_size > 5 * 1024 * 1024: # 5MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 5MB를 넘을 수 없습니다."
        )
        
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