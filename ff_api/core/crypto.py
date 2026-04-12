import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from ff_api.config.settings import settings

class AESCipher:
    def __init__(self):
        try:
            self.key = binascii.unhexlify(settings.AES_KEY)
            self.iv = binascii.unhexlify(settings.AES_IV)
        except binascii.Error:
            # Fallback for non-hex keys in development
            self.key = settings.AES_KEY.encode().ljust(32, b'\0')[:32]
            self.iv = settings.AES_IV.encode().ljust(16, b'\0')[:16]

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(data, AES.block_size))

    def decrypt(self, encrypted_data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(encrypted_data), AES.block_size)

crypto = AESCipher()
