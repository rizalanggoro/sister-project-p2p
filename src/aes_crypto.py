from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# 32-byte key for AES-256 (in production, use env or key exchange)
AES_KEY = b'0123456789abcdef0123456789abcdef'  # 32 bytes

def aes_encrypt(plaintext: bytes) -> bytes:
    iv = get_random_bytes(16)
    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv=iv)
    ciphertext = cipher.encrypt(plaintext)
    return base64.b64encode(iv + ciphertext)

def aes_decrypt(token: bytes) -> bytes:
    raw = base64.b64decode(token)
    iv = raw[:16]
    ciphertext = raw[16:]
    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv=iv)
    return cipher.decrypt(ciphertext)
