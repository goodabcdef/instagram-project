from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models import User
from schemas import UserCreate

# 비밀번호 암호화 도구 세팅
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# [기능 1] 비밀번호 암호화 함수
def get_password_hash(password):
    return pwd_context.hash(password)

# [기능 2] 이메일 중복 확인 함수
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# [기능 3] 유저 생성 (회원가입) 함수
def create_user(db: Session, user: UserCreate):
    # 1. 비밀번호 암호화
    hashed_password = get_password_hash(user.password)
    
    # 2. DB 저장용 객체 만들기
    db_user = User(
        email=user.email,
        password=hashed_password, # 암호화된 비번 저장
        nickname=user.nickname,
        provider="LOCAL"          # 일반 회원가입
    )
    
    # 3. DB에 넣고 저장
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user