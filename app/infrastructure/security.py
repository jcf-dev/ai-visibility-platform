from cryptography.fernet import Fernet
from app.infrastructure.config import settings


def get_fernet():
    return Fernet(settings.ENCRYPTION_KEY)


def encrypt_value(value: str) -> str:
    if not value:
        return value
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    if not value:
        return value
    f = get_fernet()
    return f.decrypt(value.encode()).decode()
