import asyncio
import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

AES_KEY = b"Yg&tc%DEuh6%Zc^8"
AES_IV = b"6oyZDr22E3ychjM%"

def aes_encrypt(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, 16))

def encode_varint(value):
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value & 0x7F)
    return bytes(out)

def encode_proto(uid, region, version):
    def f(tag, wire, val):
        header = encode_varint((tag << 3) | wire)
        if wire == 2:
            if isinstance(val, str): val = val.encode()
            return header + encode_varint(len(val)) + val
        return b""
    return f(1, 2, uid) + f(2, 2, region) + f(3, 2, version)

async def test_version(session, version):
    url = "https://202.81.109.65/api/v1/account?region=IND"
    payload = aes_encrypt(encode_proto("1429634330", "IND", version))
    headers = {
        "Host": "client.ind.freefiremobile.com",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11)",
        "Content-Type": "application/x-protobuf",
        "X-GA-Version": version,
        "Connection": "close"
    }
    try:
        async with session.post(url, data=payload, headers=headers, timeout=5, ssl=False) as resp:
            if resp.status == 200:
                print(f"!!! SUCCESS WITH VERSION: {version} !!!")
                return True
    except:
        pass
    return False

async def main():
    versions = ["OB45", "OB46", "OB47", "OB48", "OB49", "OB50", "OB51", "OB52", "OB53", "2.100.1", "2.101.1", "2.102.1", "2.103.1"]
    async with aiohttp.ClientSession() as session:
        for v in versions:
            if await test_version(session, v):
                return

if __name__ == "__main__":
    asyncio.run(main())
