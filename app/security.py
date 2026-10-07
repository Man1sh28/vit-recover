from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def mask_reg_no(reg_no: str) -> str:
    if len(reg_no) <= 4:
        return "****"
    return reg_no[:2] + "*" * (len(reg_no) - 4) + reg_no[-2:]

def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    shown = local[:2] if len(local) >= 2 else local[:1]
    return f"{shown}{'*' * max(3, len(local)-len(shown))}@{domain}"

def mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 4:
        return "**********"
    return "*" * (len(digits) - 4) + digits[-4:]
