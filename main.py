from fastapi import FastAPI, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine
import models
import redis
from routers import users, posts, comments, likes, bookmarks, follows, admin, search, auth

# 1. 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

# 2. FastAPI 앱 실행 (이게 먼저 나와야 @app을 쓸 수 있음)
app = FastAPI(title="인스타그램 API", version="1.0.0")

# 3. Redis 연결 설정 (필수 요건)
# (Docker로 띄운 Redis에 접속 시도)
try:
    # decode_responses=True를 하면 데이터가 byte가 아니라 string으로 나옴
    rd = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except Exception as e:
    print(f"Redis 연결 에러: {e}")
    rd = None

# 4. 사진 폴더 개방
app.mount("/static", StaticFiles(directory="static"), name="static")

# 5. 라우터(기능들) 등록
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
app.include_router(bookmarks.router)
app.include_router(follows.router)
app.include_router(admin.router)
app.include_router(search.router)
app.include_router(auth.router)

# ==========================================
# [기본 API] 서버 생존 확인
# ==========================================
@app.get("/")
def read_root():
    # static 폴더 안에 있는 index.html 파일을 사용자에게 전송
    return FileResponse("static/index.html")

# ==========================================
# [추가 API] 서버 상태 체크 + 방문자 카운트
# (Redis 활용 필수 요건 + 503 상태코드 확보용)
# ==========================================
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(response: Response):
    # Redis 클라이언트 자체가 없으면 에러
    if rd is None:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "detail": "Redis 설정 오류"}

    try:
        # Redis 서버에 '살아있니?' 물어봄 (Ping)
        if rd.ping():
            # [필수 요건] Redis를 활용해 방문자 수 1 증가시키기
            count = rd.incr("visitor_count")
            return {
                "status": "ok", 
                "redis": "connected", 
                "total_visitors": count,
                "message": "Redis가 정상 작동 중입니다."
            }
    except Exception:
        # Redis가 꺼져있거나 연결 안 되면 503 에러 리턴
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "detail": "Redis 서버에 연결할 수 없습니다."}