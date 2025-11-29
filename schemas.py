from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime  # [중요] 날짜 도구는 맨 위에서 불러와야 함

# [1] 회원가입할 때 받을 데이터
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: str

# [2] 유저 정보 보여줄 때 양식
class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    is_admin: bool

    class Config:
        from_attributes = True

# [3] 로그인 성공 시 토큰 양식
class Token(BaseModel):
    access_token: str
    token_type: str

# [4] 게시글 보여줄 때 양식
class PostResponse(BaseModel):
    id: int
    content: str
    image_url: str
    user_id: int
    created_at: datetime  # 이제 에러 안 날 겁니다

    class Config:
        from_attributes = True
        
# [5] 댓글 작성할 때 받을 데이터
class CommentCreate(BaseModel):
    post_id: int   # 어느 글에 달 건지
    content: str   # 댓글 내용

# [6] 댓글 보여줄 때 양식
class CommentResponse(BaseModel):
    id: int
    content: str
    user_id: int
    post_id: int
    created_at: datetime
    
    # 닉네임도 보여주면 좋음 (선택)
    # nickname: str 

    class Config:
        from_attributes = True
        
# [7] 좋아요/북마크 결과 양식 (구조가 똑같음)
# [추가] 좋아요/북마크 요청할 때 쓸 양식 (ID만 딱 받음)
class PostIdRequest(BaseModel):
    post_id: int

class LikeResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        
# [추가] 게시글 수정할 때 받을 데이터 (사진은 수정 안 하고 내용만)
class PostUpdate(BaseModel):
    content: str