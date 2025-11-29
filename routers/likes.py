from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies

router = APIRouter(
    prefix="/likes",
    tags=["Like (좋아요)"],
)

# [API 9] 좋아요 누르기
@router.post("", response_model=schemas.LikeResponse, status_code=status.HTTP_201_CREATED)
def create_like(
    like: schemas.PostIdRequest,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    # 이미 좋아요 눌렀는지 확인
    existing_like = db.query(models.Like).filter(
        models.Like.user_id == current_user.id,
        models.Like.post_id == like.post_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=409, detail="이미 좋아요를 눌렀습니다.")

    new_like = models.Like(user_id=current_user.id, post_id=like.post_id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return new_like

# [API 10] 좋아요 취소
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_like(
    post_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    like = db.query(models.Like).filter(
        models.Like.user_id == current_user.id,
        models.Like.post_id == post_id
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="좋아요를 누른 적이 없습니다.")

    db.delete(like)
    db.commit()
    return

# [API 11] 내가 좋아요 한 글 목록 보기
@router.get("/me", response_model=list[schemas.LikeResponse])
def read_my_likes(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Like).filter(models.Like.user_id == current_user.id).all()

# ==========================================
# [API - 31] 특정 게시글에 좋아요 누른 사람 목록 보기
# ==========================================
@router.get("/post/{post_id}", response_model=list[schemas.UserResponse])
def read_users_who_liked(
    post_id: int,
    db: Session = Depends(get_db)
):
    # 1. 해당 게시글에 달린 좋아요를 다 찾는다.
    likes = db.query(models.Like).filter(models.Like.post_id == post_id).all()
    
    # 2. 좋아요 누른 사람(owner)의 정보만 뽑아서 리스트로 준다.
    return [like.owner for like in likes]