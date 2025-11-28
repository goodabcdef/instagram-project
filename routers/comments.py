from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies

router = APIRouter(
    prefix="/comments",
    tags=["Comment (댓글)"],
)

# ==========================================
# [API 6] 댓글 작성
# ==========================================
@router.post("", response_model=schemas.CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment: schemas.CommentCreate,
    current_user: models.User = Depends(dependencies.get_current_user), # 로그인 필수
    db: Session = Depends(get_db)
):
    # 1. 게시글이 진짜 있는지 확인
    post = db.query(models.Post).filter(models.Post.id == comment.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    # 2. 댓글 저장
    db_comment = models.Comment(
        content=comment.content,
        user_id=current_user.id,
        post_id=comment.post_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return db_comment

# ==========================================
# [API 7] 댓글 목록 조회 (특정 게시글의 댓글만)
# ==========================================
@router.get("", response_model=list[schemas.CommentResponse])
def read_comments(post_id: int, db: Session = Depends(get_db)):
    # 해당 post_id를 가진 댓글만 가져오기
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()

# ==========================================
# [API 8] 댓글 삭제
# ==========================================
@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 댓글 찾기
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글이 없습니다.")
    
    # 2. 내 댓글인지 확인 (관리자면 패스)
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    # 3. 삭제
    db.delete(comment)
    db.commit()
    return