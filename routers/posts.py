from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config( 
  cloud_name = os.getenv("CLOUD_NAME"), 
  api_key = os.getenv("CLOUD_API_KEY"), 
  api_secret = os.getenv("CLOUD_API_SECRET") 
)

router = APIRouter(
    prefix="/posts",
    tags=["Post (게시글)"],
)

# ==========================================
# [API 4] 게시글 작성 (Cloudinary 업로드 적용)
# ==========================================
@router.post("", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    content: str = Form(None),
    file: UploadFile = File(...),
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    # [보안 1] 415 에러: 이미지 파일이 아니면 거절
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="이미지 파일(jpg, png 등)만 업로드 가능합니다."
        )

    # [보안 2] 413 에러: 파일 크기가 5MB 넘으면 거절
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0) # 커서를 다시 맨 앞으로 (중요!)
    
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 5MB를 넘을 수 없습니다."
        )
        
    # [수정됨] Cloudinary로 업로드
    try:
        # 파일을 클라우드로 전송 (단 한 줄로 끝!)
        upload_result = cloudinary.uploader.upload(file.file)
        
        # 업로드된 인터넷 주소(URL) 가져오기
        image_url = upload_result.get("secure_url")
        
    except Exception as e:
        print(f"업로드 에러: {e}")
        raise HTTPException(status_code=500, detail="이미지 업로드에 실패했습니다.")
    
    # DB에 게시글 정보 저장 (URL은 이제 Cloudinary 주소)
    db_post = models.Post(
        content=content,
        image_url=image_url, 
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
    return db.query(models.Post).order_by(models.Post.created_at.desc()).all()

# ==========================================
# [API 17] 특정 유저가 쓴 글 모아보기 (프로필용)
# ==========================================
@router.get("/user/{user_id}", response_model=list[schemas.PostResponse])
def read_user_posts(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Post).filter(models.Post.user_id == user_id).order_by(models.Post.created_at.desc()).all()

# ==========================================
# [API 18] 게시글 상세 조회
# ==========================================
@router.get("/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return post

# ==========================================
# [API 19] 게시글 수정
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

    if post.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    
    db.delete(post)
    db.commit()
    return