from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies

router = APIRouter(
    prefix="/follows",
    tags=["Follow (팔로우)"],
)

# ==========================================
# [API 21] 팔로우 하기 (친구 추가)
# ==========================================
@router.post("/{target_id}", status_code=status.HTTP_201_CREATED)
def follow_user(
    target_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 자기 자신을 팔로우하는지 체크 (방지)
    if target_id == current_user.id:
        raise HTTPException(status_code=400, detail="자기 자신은 팔로우할 수 없습니다.")

    # 2. 상대방 유저가 존재하는지 찾기
    target_user = db.query(models.User).filter(models.User.id == target_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="해당 유저를 찾을 수 없습니다.")

    # 3. 이미 팔로우 중인지 체크
    # (current_user.following 리스트 안에 상대방이 있는지 확인)
    if target_user in current_user.following:
        raise HTTPException(status_code=409, detail="이미 팔로우 중입니다.")

    # 4. 팔로우 (내 팔로잉 목록에 상대방 추가)
    current_user.following.append(target_user)
    db.commit()
    
    return {"message": "팔로우 성공"}

# ==========================================
# [API 22] 언팔로우 하기 (친구 끊기)
# ==========================================
@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    target_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    target_user = db.query(models.User).filter(models.User.id == target_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="유저가 없습니다.")

    # 팔로우 목록에 없으면 에러
    if target_user not in current_user.following:
        raise HTTPException(status_code=400, detail="팔로우하고 있지 않습니다.")

    # 목록에서 제거
    current_user.following.remove(target_user)
    db.commit()
    return

# ==========================================
# [API 23] 나를 팔로우한 사람 목록 (팔로워)
# ==========================================
@router.get("/followers", response_model=list[schemas.UserResponse])
def read_followers(
    current_user: models.User = Depends(dependencies.get_current_user),
):
    return current_user.followers

# ==========================================
# [API 24] 내가 팔로우한 사람 목록 (팔로잉)
# ==========================================
@router.get("/followings", response_model=list[schemas.UserResponse])
def read_followings(
    current_user: models.User = Depends(dependencies.get_current_user),
):
    return current_user.following