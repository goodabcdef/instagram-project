from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# [1] 팔로우 테이블 (N:M 관계)
follow_table = Table(
    'follows', Base.metadata,
    Column('follower_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('following_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# [2] 해시태그 연결 테이블 (게시글-해시태그 N:M)
post_hashtags = Table(
    'post_hashtags', Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('hashtag_id', Integer, ForeignKey('hashtags.id'), primary_key=True)
)

# [3] 유저 테이블
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True) # 이메일
    password = Column(String(255), nullable=True)        # 비밀번호
    nickname = Column(String(50), index=True)            # 닉네임 (검색용)
    image_url = Column(String(255), nullable=True)       # 프로필 사진
    is_admin = Column(Boolean, default=False)            # 관리자 여부
    
    provider = Column(String(20), default="LOCAL")       # 가입경로 (LOCAL, KAKAO, FIREBASE)
    provider_id = Column(String(100), nullable=True)     # 소셜 ID
    created_at = Column(DateTime, default=func.now())    # 가입일

    # 내가 쓴 글, 댓글, 좋아요, 북마크
    posts = relationship("Post", back_populates="owner")
    comments = relationship("Comment", back_populates="owner")
    likes = relationship("Like", back_populates="owner")
    bookmarks = relationship("Bookmark", back_populates="owner")

    # 팔로워/팔로잉 관계
    followers = relationship(
        "User", secondary=follow_table,
        primaryjoin=id==follow_table.c.following_id,
        secondaryjoin=id==follow_table.c.follower_id,
        backref="following"
    )

# [4] 게시글 테이블
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)                               # 본문
    image_url = Column(String(255))                      # 사진 (1장)
    user_id = Column(Integer, ForeignKey("users.id"))    # 작성자
    created_at = Column(DateTime, default=func.now())    # 작성일
    
    owner = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete")
    likes = relationship("Like", back_populates="post", cascade="all, delete")
    bookmarks = relationship("Bookmark", back_populates="post", cascade="all, delete")
    
    # 해시태그 관계 설정
    hashtags = relationship("Hashtag", secondary=post_hashtags, back_populates="posts")

# [5] 댓글 테이블
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=func.now())

    owner = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

# [6] 좋아요 테이블
class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=func.now())
    
    owner = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")

# [7] 북마크 테이블 (보관함)
class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    created_at = Column(DateTime, default=func.now())

    owner = relationship("User", back_populates="bookmarks")
    post = relationship("Post", back_populates="bookmarks")

# [8] 해시태그 테이블 (검색용)
class Hashtag(Base):
    __tablename__ = "hashtags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True) # 태그명 (예: #여행)

    posts = relationship("Post", secondary=post_hashtags, back_populates="hashtags")