from typing import Protocol, runtime_checkable
import hmac
import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

@runtime_checkable
class ISecurityProvider(Protocol):
    
    def hash_secret(self, secret: str, salt: str = "") -> str:
        ...

    def verify_secret(self, plain_secret: str, hashed_secret: str, salt: str = "") -> bool:
        ...

class Argon2SecurityProvider:
    
    def __init__(self):
        self.ph = PasswordHasher(
            time_cost=3, memory_cost=65536, parallelism=4,
            hash_len=32, salt_len=16
        )

    def hash_secret(self, secret: str, salt: str = "") -> str:
        
        return self.ph.hash(secret)

    def verify_secret(self, plain_secret: str, hashed_secret: str, salt: str = "") -> bool:
        try:
            return self.ph.verify(hashed_secret, plain_secret)
        except (VerifyMismatchError, Exception):
            return False

class HMACSecurityProvider:
    
    def hash_secret(self, secret: str, salt: str = "") -> str:
        if not salt:
            raise ValueError("HMAC requires a salt (key)")
        return hmac.new(salt.encode(), secret.encode(), hashlib.sha256).hexdigest()

    def verify_secret(self, plain_secret: str, hashed_secret: str, salt: str = "") -> bool:
        if not salt:
            return False
        expected = self.hash_secret(plain_secret, salt)
        return hmac.compare_digest(expected, hashed_secret)
