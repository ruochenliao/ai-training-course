import warnings
# 抑制 passlib 中 pkg_resources 的弃用警告
warnings.filterwarnings("ignore", message="pkg_resources is deprecated", category=UserWarning)

from passlib import pwd
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password() -> str:
    return pwd.genword()
