from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies

router = APIRouter(
    prefix="/bookmarks",
    tags=["Bookmark (보관함)"],
)

# [API 12] 북마크 저장
@router.post("", response_model=schemas.BookmarkResponse, status_code=status.HTTP_201_CREATED)
def create_bookmark(
    bookmark: schemas.PostIdRequest,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == current_user.id,
        models.Bookmark.post_id == bookmark.post_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="이미 보관함에 있습니다.")

    new_bookmark = models.Bookmark(user_id=current_user.id, post_id=bookmark.post_id)
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)
    return new_bookmark

# [API 13] 북마크 취소
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bookmark(
    post_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == current_user.id,
        models.Bookmark.post_id == post_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="보관함에 없는 글입니다.")

    db.delete(bookmark)
    db.commit()
    return

# [API 14] 내 보관함 보기
@router.get("/me", response_model=list[schemas.BookmarkResponse])
def read_my_bookmarks(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Bookmark).filter(models.Bookmark.user_id == current_user.id).all()