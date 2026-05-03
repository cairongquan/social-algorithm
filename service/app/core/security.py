"""密码散列与 JWT 鉴权工具。"""

import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = "social-algorithm-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """对明文密码做 SHA-256 散列。"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码与散列值是否匹配。"""
    return hash_password(password) == password_hash

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建带过期时间的访问令牌。"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """解码 JWT；非法令牌返回 None。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
