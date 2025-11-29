from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies

router = APIRouter(
    prefix="/admin",
    tags=["Admin (관리자)"],
)

# [관리자 체크 도구]
def check_admin(current_user: models.User):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="관리자 권한이 없습니다.")

# ==========================================
# [API 25] 전체 회원 조회 (관리자용)
# ==========================================
@router.get("/users", response_model=list[schemas.UserResponse])
def read_all_users(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user) # 관리자 아니면 쫓아냄
    return db.query(models.User).all()

# ==========================================
# [API 26] 회원 강제 탈퇴 (밴)
# ==========================================
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def ban_user(
    user_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저가 없습니다.")
        
    db.delete(user)
    db.commit()
    return

# ==========================================
# [API 27] 게시글 강제 삭제
# ==========================================
@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_admin(
    post_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    check_admin(current_user)
    
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글이 없습니다.")
        
    db.delete(post)
    db.commit()
    return