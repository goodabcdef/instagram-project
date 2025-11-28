from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
import schemas, crud, models
import dependencies # 방금 만든 도구함 불러오기

# 라우터 별명 설정 (URL 앞에 /users가 자동으로 붙거나, 태그가 붙음)
router = APIRouter(
    tags=["User (회원)"], # Swagger에서 섹션 이름
)

# 회원가입
@router.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
    return crud.create_user(db=db, user=user)

# 로그인
@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not crud.pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 틀렸습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = dependencies.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# 내 정보 조회
@router.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(dependencies.get_current_user)):
    return current_user