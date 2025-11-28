from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 도커 MySQL 접속 정보
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1234@127.0.0.1:3306/instagram"

# DB 연결 엔진 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# DB 세션(대화창) 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델들의 조상님 (이걸 상속받아서 테이블을 만듦)
Base = declarative_base()

# DB 세션을 가져오는 함수 (API 만들 때 계속 쓸 예정)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()