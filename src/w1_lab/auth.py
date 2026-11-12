import hashlib
import secrets # 标准库，提供密码学安全的随机数（token_bytes 生成盐，compare_digest 做恒定时间比较）。
from datetime import datetime,timedelta,timezone

import jwt

SECRET_KEY = "dev-only-change-me-in-production" # JWT签名密钥，当前值是开发占位符，生产必须换成随机长密钥
# 泄露这个key等于任何人都能伪造任意用户的token
ALGORITHM="HS256"  # JWT签名算法：HMAC+SHA-256,对称算法，签名和验证用同一个SECRET_KEY,适合单体服务
TOKEN_EXPIPE_HOURS=24
PBKDF2_ITERATIONS=200_000 # 迭代次数20万次，迭代次数越高越慢，暴力破解成本越高
 
def hash_password(password:str)->str:
    salt=secrets.token_bytes(16) # 生成16字节随机盐，盐的作用：即使两个用户密码相同，哈希结果也不同，防止彩虹表攻击。
    digest=hashlib.pbkdf2_hmac(
        "sha256",password.encode(),salt,PBKDF2_ITERATIONS # 用PBKDF2-HMAC-SHA256计算哈希，返回bytes类型的派生密钥
    )
    return f"{salt.hex()}${digest.hex()}" # 把盐和哈希转成十六进制字符串

def verify_password(password:str,stored:str)->bool:
    salt_hex,digest_hex=stored.split("$",1)
    digest=hashlib.pbkdf2_hmac(
        "sha256",password.encode(),bytes.fromhex(salt_hex),PBKDF2_ITERATIONS
    ) # 用同样的盐和迭代次数重新计算输入密码的哈希
    return secrets.compare_digest(digest.hex(),digest_hex) # 恒定时间比较，防止时序攻击（攻击者会通过响应时间差逐字节猜测）

def create_token(username:str)->str: # 签发JWT
    payload={
        "sub":username,
        "exp":datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIPE_HOURS), # 当前UTC时间和24小时后过期
    } # payload是Base64编码，不是加密，任何人都能解码看到sub和exp，不要放敏感信息
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
   # 用 SECRET_KEY 和 HS256 对 payload 签名，生成 JWT 字符串（形如 xxx.yyy.zzz）
def decode_token(token:str)->str: # 验证并解析JWT
    payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM]) # 解码并验证JWT，校验exp是否过期，校验签名是否正确
    # algorithms=[ALGORITHM]：必须显式指定允许的算法，否则有 算法混淆攻击 风险（攻击者把 alg 改成 none 或非对称算法来绕过签名）。这是 PyJWT 的强制要求。
    return str(payload["sub"])