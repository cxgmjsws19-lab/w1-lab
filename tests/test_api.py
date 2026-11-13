from collections.abc import Iterator
import concurrent.futures
from pathlib import Path
from datetime import datetime,timedelta,timezone
import time

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session,sessionmaker

from w1_lab import cache
from w1_lab.api import app,get_db
from w1_lab.auth import ALGORITHM,SECRET_KEY
from w1_lab.models import LogEntry
from w1_lab.db import Base
from w1_lab.parser import LogFormatError

GOOD_LINE = "2026-11-10T09:00:00 10.0.0.1 GET /api/users 200 1234 45.2" #一条合法的日志样本，多个测试复用。

@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:   # 自动清缓存
    cache.clear() #测试前清空缓存，防止上一个测试残留。
    yield          #把控制权交给测试函数执行。
    cache.clear()   #测试后再清一次，保证隔离

@pytest.fixture
def client(tmp_path:Path) -> Iterator[TestClient]:  #定义名为 client 的 fixture，接收 pytest 内置的 tmp_path（每个测试独立的临时目录）。
    engine=create_engine(               #创建一个文件型 SQLite 引擎，数据库在临时目录的 test.db。
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread":False},
    )
    Base.metadata.create_all(engine)        #根据 ORM 模型元数据在测试库里建表。
    TestSession=sessionmaker(bind=engine,expire_on_commit=False)  #创建会话工厂，绑定到测试引擎。

    def override_get_db()->Iterator[Session]:        #定义替代的数据库依赖，每次请求打开一个会话，请求结束自动关闭。
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db #关键——用 FastAPI 的依赖覆盖机制，把应用真正的 get_db 替换成测试版，让请求使用测试数据库而非生产库。

    test_client = TestClient(app)#用被测 app 创建测试客户端。
    register = test_client.post(      #注册一个测试用户，拿到返回（应含 token）。
        "/register", json={"username": "tester", "password": "pw123"}
    )
    test_client.headers["Authorization"] = (  #把注册返回的 access_token 设置到客户端默认请求头，之后所有请求自动带认证。
        f"Bearer {register.json()['access_token']}"
    )

    yield test_client  #把 test_client 交给测试使用；
    app.dependency_overrides.clear()

def test_health(client:TestClient)->None:     #健康检查接口返回 200 且 body 为 {"status":"ok"}。
    response=client.get("/health")
    assert response.status_code==200
    assert response.json()=={"status":"ok"}

def test_create_entry_returns_201(client:TestClient)->None: #提交合法日志行，期望创建成功（201），返回体里的解析状态码是 200。
    response=client.post("/entries",json={"line":GOOD_LINE})
    assert response.status_code==201
    assert response.json()["status"]==200

def test_create_entry_rejects_bad_line(client:TestClient)->None:#提交非法行，期望 422（不可处理实体），错误信息含"期望"（格式提示）。
    response =client.post("/entries",json={"line":"bad line"})
    assert response.status_code==422
    assert "期望" in response.json()["detail"]

def test_stats_starts_empty(client:TestClient)->None: #新库统计初始 total 为 0
    assert client.get("/entries/stats").json()["total"]==0

def test_stats_counts_after_writes(client:TestClient)->None:#写入两条后统计 total 应为 2。
    client.post("/entries",json={"line":GOOD_LINE})
    client.post("/entries",json={"line":GOOD_LINE})
    assert client.get("/entries/stats").json()["total"]==2

def test_old_routes_are_gone(client:TestClient)->None:#旧版路由 /parse、/stats 已移除，返回 404（验证迁移/重构）。
    assert client.post("/parse",json={"line":GOOD_LINE}).status_code==404
    assert client.get("/stats").status_code==404

#新建一个没有设置认证头的客户端 fresh，发请求应返回 401，且响应头 WWW-Authenticate 为 Bearer（符合规范）。
def test_entries_requires_token(client: TestClient) -> None:
    fresh = TestClient(app)
    response = fresh.post("/entries", json={"line": GOOD_LINE})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


#第一次请求统计缓存未命中（MISS），第二次命中（HIT），验证缓存生效。
def test_stats_cache_hit(client: TestClient) -> None:
    first = client.get("/entries/stats")
    assert first.headers["x-cache"] == "MISS"
    second = client.get("/entries/stats")
    assert second.headers["x-cache"] == "HIT"


#先预热缓存（第二次为 HIT）；写入新条目后缓存应失效，下次请求变回 MISS，验证写操作会清缓存。
def test_write_invalidates_cache(client: TestClient) -> None:
    client.get("/entries/stats")
    assert client.get("/entries/stats").headers["x-cache"] == "HIT"

    client.post("/entries", json={"line": GOOD_LINE})

    assert client.get("/entries/stats").headers["x-cache"] == "MISS"


#手工签发一个 token，sub 为用户 tester，exp 设为1小时前（已过期），用项目相同的密钥和算法签名（伪造有效签名但过期）。
def test_expired_token(client:TestClient)->None:
    expired=jwt.encode(
        {"sub":"tester","exp":datetime.now(timezone.utc)-timedelta(hours=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response=client.post(         #用过期 token 请求，应 401，错误详情为"token已过期"。
        "/entries",
        json={"line":GOOD_LINE},
        headers={"Authorization":f"Bearer {expired}"},
    )
    assert response.status_code==401
    assert response.json()["detail"]=="token 已过期"

def test_parse_error_becomes_422(  #定义测试，使用 monkeypatch fixture 动态替换函数。
        client:TestClient,
        monkeypatch:pytest.MonkeyPatch,
)->None:
    def boom(line:str)->LogEntry:  #定义一个假解析函数，一调用就抛 LogFormatError。
        raise LogFormatError("模拟解析失败")

#把 w1_lab.api 模块里的 parse_line 替换成 boom。这样请求时调用的就是抛异常的版本（打补丁），无需真实构造坏数据。
    monkeypatch.setattr("w1_lab.api.parse_line", boom)

#发请求，验证 LogFormatError 被应用层捕获并转换成 422，且错误信息原样传递。
    response = client.post("/entries", json={"line": "随便什么"})
    assert response.status_code == 422
    assert response.json()["detail"] == "模拟解析失败"


# ── 单条查询 + 缓存三问题 ──────────────────────────────────────────

def test_get_entry_returns_200(client: TestClient) -> None:
    created = client.post("/entries", json={"line": GOOD_LINE}).json()  #先 POST /entries 创建一条记录。.json() 取响应体（一个 dict，含 ip、status、path 等字段）。
    response = client.get("/entries/1") #测试库是全新空库，第一条记录主键必为 1（SQLite 自增从 1 开始）。
    assert response.status_code == 200
    assert response.json()["ip"] == created["ip"]


def test_get_missing_entry_caches_null(client: TestClient) -> None:
    """穿透防护：第二次请求不该再打库，靠哨兵值挡住。"""
    first = client.get("/entries/999999")
    assert first.status_code == 404

    # 关键断言：哨兵值真的进了缓存（只断言两次 404 无法证明任何事）
    assert cache.get("entry:999999") == cache.NULL_SENTINEL

    second = client.get("/entries/999999")
    assert second.status_code == 404


def test_get_entry_caches_real_value(client: TestClient) -> None: #验证"查到数据后会被缓存"。
    client.post("/entries", json={"line": GOOD_LINE})  #先创建记录，再查询一次（触发查库 + 回填缓存）
    client.get("/entries/1")
    cached = cache.get("entry:1")
    assert cached is not None
    assert cached != cache.NULL_SENTINEL


def test_stats_route_not_shadowed(client: TestClient) -> None:    #验证路由顺序问题（就是我们之前讲的"静态路径 vs 动态路径"）
    """防护性测试：/entries/{entry_id} 若被注册到 /entries/stats 之前，此测试立刻红。"""
    assert client.get("/entries/stats").status_code == 200


def test_stats_single_flight(     #防击穿
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """防击穿：5 个并发请求同时遇到缓存失效，只应回填一次（一次查库）。"""
    cache.delete("stats:v1")  #手动删除统计缓存，制造"缓存失效"状态。
    set_calls = {"n": 0}
    real_set = cache.set  #real_set = cache.set：保存原始 set 函数引用，后面要调它做真实写入。

#定义一个计数包装器
    def counting_set(key: str, value: str, ttl: int = 60) -> None:
        set_calls["n"] += 1
        time.sleep(0.05)  # 拉长临界区，放大竞态窗口
        real_set(key, value, ttl)  #调用真正的cache.set完成写入

    monkeypatch.setattr("w1_lab.api.cache.set", counting_set)  #把 w1_lab.api 模块里的 cache.set 替换成 counting_set。

#并发发起5个请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = [f.result() for f in [pool.submit(client.get, "/entries/stats") for _ in range(5)]]

    assert all(r.status_code == 200 for r in results)
    assert set_calls["n"] == 1  # 没有锁的话会是 5