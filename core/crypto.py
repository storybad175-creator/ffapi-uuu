from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from config.settings import AES_KEY, AES_IV

class AESCipher:
    def __init__(self):
        self.key = AES_KEY
        self.iv = AES_IV

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(data, AES.block_size))

    def decrypt(self, encrypted_data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(encrypted_data), AES.block_size)

crypto = AESCipher()
