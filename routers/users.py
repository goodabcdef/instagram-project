from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordRequestForm  # <--- [중요] 이 줄이 꼭 있어야 합니다!
from sqlalchemy.orm import Session
from database import get_db
import schemas, crud, models, dependencies
import shutil
import os

# 사진 저장 폴더 설정
UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

# [추가 import] 파일 업로드 기능을 위해 필요
from fastapi import File, UploadFile, Form
import shutil
import os

# 사진 저장 경로 설정 (없으면 만들기)
UPLOAD_DIR = "static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==========================================
# [API 15] 내 프로필 수정 (닉네임, 프사)
# ==========================================
@router.patch("/me", response_model=schemas.UserResponse)
def update_profile(
    nickname: str = Form(None),                  # 닉네임 (선택)
    file: UploadFile = File(None),               # 프로필 사진 (선택)
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 닉네임 변경 요청이 있으면 수정
    if nickname:
        current_user.nickname = nickname
    
    # 2. 사진 변경 요청이 있으면 저장 후 수정
    if file:
        filename = f"profile_{current_user.id}_{file.filename}"
        file_path = f"{UPLOAD_DIR}/{filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        current_user.image_url = f"/static/images/{filename}"

    db.commit()
    db.refresh(current_user)
    return current_user

# ==========================================
# [API 16] 회원 탈퇴
# ==========================================
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    current_user: models.User = Depends(dependencies.get_current_user),
    db: Session = Depends(get_db)
):
    # DB에서 나 자신을 삭제
    db.delete(current_user)
    db.commit()
    return

# ==========================================
# [API - 30] 로그아웃
# ==========================================
@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: models.User = Depends(dependencies.get_current_user)):
    # 프론트엔드(앱)에서 토큰을 삭제하면 그게 바로 로그아웃입니다.
    # 나중에 Redis를 쓴다면 여기서 해당 토큰을 블랙리스트에 추가합니다.
    return {"message": "로그아웃 성공! 토큰을 삭제해주세요."}