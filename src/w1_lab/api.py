from fastapi import FastAPI, HTTPException, Depends, Response, Header
from pydantic import BaseModel
from sqlalchemy import func, select
from collections.abc import Iterator
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer

from . import cache
from .db import LogEntryRow, SessionLocal, UserRow
from .models import LogEntry
from .parser import LogFormatError, parse_line
from .auth import create_token, decode_token, hash_password, verify_password

import jwt

app = FastAPI(title="w1-lab API")  # 创建FastAPI实例
STATS_CACHE_KEY = "stats:v1"  # 以后StatsResponse结构变了，把key改成v2，旧缓存自动失效，缓存版本化小技巧


def get_db() -> Iterator[Session]:  # 数据库会话依赖，作为 Depends(get_db) 的依赖源。
    with SessionLocal() as session:  # 准备：开连接，创建会话
        yield session  # 交给接口函数，暂停


bearer_scheme=HTTPBearer(auto_error=False) #HTTPBearer 会在 OpenAPI 文档（Swagger UI）里自动生成一个漂亮的 🔒 Authorize 按钮。你点开它输入 Token 后，Swagger 会自动帮你带上 Bearer 前缀。
def get_current_user(
        credentials:HTTPAuthorizationCredentials | None =Depends(bearer_scheme)
)->str:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="缺少 Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="token 已过期") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="token 无效") from exc
    
class ParseRequest(BaseModel):  # 创建日志请求体：{"line": "..."}。
    line: str


class HealthResponse(BaseModel):  # 健康检查响应：{"status": "ok"}
    status: str


class RegisterRequest(BaseModel):  # 注册/登录请求体，注册和登录复用同一个模型
    username: str
    password: str


class TokenResponse(BaseModel):  # 令牌响应
    access_token: str
    token_type: str = "bearer"


@app.get("/health", response_model=HealthResponse)  # 注册 GET /health 路由
def health() -> HealthResponse:
    return HealthResponse(status="ok")  # 负载均衡器、K8s 探针、监控系统定期打这个接口判断服务活着


@app.post("/entries", response_model=LogEntry, status_code=201)  # 注册 POST /entries
def create_entry(
    request: ParseRequest,  # 请求体参数，FastAPI 自动从 JSON body 解析成 ParseRequest
    response: Response,
    session: Session = Depends(get_db),  # 数据库会话，由 get_db 提供
    current_user: str = Depends(get_current_user),
) -> LogEntry:
    try:
        entry = parse_line(request.line)  # 解析请求里的日志行，得到 LogEntry
    except LogFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    session.add(LogEntryRow(**entry.model_dump()))
    session.commit()
    cache.delete(STATS_CACHE_KEY)  # 保证数据更新
    return entry


class StatsResponse(BaseModel):
    total: int
    by_status: dict[int, int]


@app.get("/entries/stats", response_model=StatsResponse)
def entries_stats(
    response: Response,
    session: Session = Depends(get_db),
) -> StatsResponse:
    cached = cache.get(STATS_CACHE_KEY)
    if cached is not None:
        response.headers["X-cache"] = "HIT"
        return StatsResponse.model_validate_json(cached)  # 经历了 JSON->对象->JSON 的往返

    response.headers["X-cache"] = "MISS"  # 走到这里说明缓存未命中

    total = session.scalar(select(func.count()).select_from(LogEntryRow)) or 0
    rows = session.execute(
        select(LogEntryRow.status, func.count()).group_by(LogEntryRow.status)
    ).all()

    result = StatsResponse(total=total, by_status={s: c for s, c in rows})
    cache.set(STATS_CACHE_KEY, result.model_dump_json())
    return result


@app.post("/register", response_model=TokenResponse, status_code=201)  # 注册
def register(
    request: RegisterRequest,
    session: Session = Depends(get_db),
) -> TokenResponse:
    exists = session.scalar(
        select(UserRow).where(UserRow.name == request.username)
    )
    if exists is not None:
        raise HTTPException(status_code=409, detail="用户名已存在")

    session.add(
        UserRow(name=request.username, password_hash=hash_password(request.password))
    )
    session.commit()
    return TokenResponse(access_token=create_token(request.username))


@app.post("/login", response_model=TokenResponse)
def login(
    request: RegisterRequest,
    session: Session = Depends(get_db),
) -> TokenResponse:
    user = session.scalar(
        select(UserRow).where(UserRow.name == request.username)
    )
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return TokenResponse(access_token=create_token(request.username))