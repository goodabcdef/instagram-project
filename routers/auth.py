from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, dependencies
import requests
import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["Auth (소셜로그인)"],
)

# ==========================================
# [설정] 카카오 디벨로퍼스에서 복사한 키를 여기에 넣으세요!
# ==========================================
KAKAO_REST_API_KEY = "f544e1a61c7ad46a87928fdf008daa1f"
REDIRECT_URI = "http://localhost:8000/auth/kakao/callback"

# ==========================================
# [API 33] 카카오 로그인 페이지 주소 주기
# ==========================================
@router.get("/kakao")
def kakao_login_url():
    # 사용자가 이 주소로 이동하면 카카오 로그인 화면이 뜸
    url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"
    return {"url": url}

# ==========================================
# [API 34] 카카오가 결과(Code)를 보내주는 곳
# ==========================================
@router.get("/kakao/callback", response_model=schemas.Token)
def kakao_callback(code: str, db: Session = Depends(get_db)):
    # 1. 토큰 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    token_res = requests.post(token_url, data=data)
    
    # [디버깅] 여기서 에러 내용을 터미널에 출력합니다!
    print("카카오 토큰 응답:", token_res.json()) 

    # 토큰 발급에 실패했으면 멈춤
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="카카오 토큰 발급 실패! 터미널 로그를 확인하세요.")

    access_token = token_res.json().get("access_token")

    # 2. 유저 정보 요청
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_res = requests.get(user_info_url, headers=headers)
    
    # [디버깅] 유저 정보 응답 출력
    print("카카오 유저 정보:", user_res.json())

    user_info = user_res.json()
    kakao_account = user_info.get("kakao_account")
    
    # 여기서 정보가 없으면 에러 처리
    if not kakao_account:
        raise HTTPException(status_code=400, detail="카카오 유저 정보를 불러올 수 없습니다.")

    # (이 아래 코드는 기존과 동일합니다)
    kakao_id = str(user_info.get("id"))
    nickname = kakao_account.get("profile", {}).get("nickname", "카카오유저")
    email = kakao_account.get("email", f"{kakao_id}@kakao.com")

    # 3. DB 확인 및 회원가입
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(
            email=email,
            nickname=nickname,
            provider="KAKAO",
            provider_id=kakao_id,
            password=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = dependencies.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# [설정] 파이어베이스 키 파일 연결
# ==========================================
try:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
except ValueError:
    pass # 이미 초기화되어 있으면 패스

# [양식] 프론트엔드에서 보낼 토큰 양식
class FirebaseLoginRequest(BaseModel):
    id_token: str

# ==========================================
# [API 35] 파이어베이스 로그인 (구글 등)
# ==========================================
@router.post("/firebase", response_model=schemas.Token)
def firebase_login(request: FirebaseLoginRequest, db: Session = Depends(get_db)):
    try:
        # 1. 프론트엔드(앱)에서 보낸 토큰이 진짜인지 검사
        decoded_token = firebase_auth.verify_id_token(request.id_token)
        
        # 2. 토큰에서 유저 정보 뽑기
        uid = decoded_token['uid']
        email = decoded_token.get('email', f"{uid}@firebase.com")
        # 닉네임이 없으면 이메일 앞부분 사용
        nickname = decoded_token.get('name', email.split("@")[0]) 

    except Exception:
        raise HTTPException(status_code=401, detail="유효하지 않은 파이어베이스 토큰입니다.")

    # 3. 우리 DB에 있는지 확인
    user = db.query(models.User).filter(models.User.email == email).first()

    # 4. 없으면 자동 회원가입
    if not user:
        user = models.User(
            email=email,
            nickname=nickname,
            provider="FIREBASE",
            provider_id=uid,
            password=None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 5. 우리 서버 토큰 발급
    access_token = dependencies.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}