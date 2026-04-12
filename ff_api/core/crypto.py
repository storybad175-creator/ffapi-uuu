import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from ff_api.config.settings import settings

class AESCipher:
    def __init__(self):
        # Attempt to use raw keys from settings first
        key_raw = settings.AES_KEY
        iv_raw = settings.AES_IV

        # Check if they are hex strings
        try:
            self.key = binascii.unhexlify(key_raw)
        except binascii.Error:
            self.key = key_raw.encode()

        try:
            self.iv = binascii.unhexlify(iv_raw)
        except binascii.Error:
            self.iv = iv_raw.encode()

        # Ensure correct lengths (AES-128: 16, AES-192: 24, AES-256: 32)
        if len(self.key) not in [16, 24, 32]:
            self.key = self.key.ljust(32, b'\0')[:32]
        if len(self.iv) != 16:
            self.iv = self.iv.ljust(16, b'\0')[:16]

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(pad(data, AES.block_size))

    def decrypt(self, encrypted_data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(encrypted_data), AES.block_size)

crypto = AESCipher()
