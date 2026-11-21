# w1-lab

一个日志收集与统计服务：接收原始访问日志行，解析、校验、入库，并提供带缓存的统计查询。
**不是一个 CRUD 练习**——它的重点是**边界处理、可观测性和可部署性**。

## 它解决什么

原始访问日志是纯文本，直接存数据库既没法查询也没法规整。这个服务把一行日志

```
2026-11-20T10:00:00+08:00 1.2.3.4 GET /api/users 200 1234 45.2
```

变成一条结构化记录（IP / 时间 / 方法 / 路径 / 状态码 / 大小 / 延迟），并在入口处挡掉脏数据。

## 技术上做了什么

**分层架构**

`api`（HTTP）→ `parser`（纯业务）/ `auth`（鉴权）/ `db`（ORM）/ `cache`（缓存）→ `models`（契约）
依赖单向，底层不 import 上层，所以业务逻辑能脱离 web 框架单独测试。

**三层校验，越靠前拦代价越小**

| 层 | 管什么 | 不合法时 |
|---|---|---|
| `parser.parse_line` | 字段数量、时间必须带时区 | 422 |
| `models.LogEntry`（pydantic） | IP 格式（IPv4/IPv6）、状态码 100–599、数值非负 | 422 |
| PostgreSQL | NOT NULL / 外键 / 类型 | 500（不该发生） |

**缓存的三个经典问题都做了防护**

| 问题 | 做法 |
|---|---|
| 穿透（查不存在的数据） | 空结果也写缓存，用 `__NULL__` 哨兵区分「没缓存」和「确实不存在」 |
| 击穿（热点 key 过期瞬间） | per-key 锁 + 双重检查，**实测回填次数从 5 次降到 1 次** |
| 雪崩（大批 key 同时过期） | TTL 加随机抖动，**实测 TTL 为 60/63/64/65/66** |

缓存放在外部 Redis，**不是进程内存**——重启 api 后缓存仍命中，这是它存在的唯一理由。

**时区正确性**

`ts` 列是 `timestamptz` 而不是 `timestamp`，入口拒绝不带时区的时间。
原因：`timestamp without time zone` 最可怕的不是「存不下时区」，**而是它根本不报错**——
同一列会混进两种语义，从数据本身分辨不出来。

**可观测性**

健康检查分两层：

| 端点 | 查什么 | 挂了以后 |
|---|---|---|
| `/health` | 什么都不查，只证明进程活着 | 该重启 |
| `/readyz` | **真的执行 `SELECT 1`** | 摘流量、报警，**不重启** |

实测：停掉数据库后 `/health` 返回 200（进程确实活着），`/readyz` 返回 503（如实报告依赖不可用）。
把两者混成一个端点，数据库抖动就会导致所有实例被误判死亡并重启。

**容器化**

- 多阶段构建：**375MB → 250MB**（省掉的是 uv/pip 和构建缓存）
- 四服务编排：nginx（TLS 终止 + 反代）+ api + postgres + redis
- **只有 nginx 对外暴露 80/443**，其余服务只在容器网络内可达
- 健康检查 + `restart: unless-stopped` + 日志轮转（`10m × 3`）+ 防火墙规则

**工程规范**

- 30 个测试，`mypy` 严格模式零错误
- alembic 迁移链，`alembic check` 纳入门禁（已开启 `compare_type`，能检测列类型漂移）
- GitHub Actions：push 触发类型检查 + 测试 + 镜像构建

## 怎么跑起来

```powershell
git clone https://github.com/cxgmjsws19-lab/w1-lab.git
cd w1-lab
# 生成自签证书 → 起服务 → 跑迁移 → 验证，完整步骤见 DEPLOY.md
```

**详细步骤（含每个坑的原因）：[DEPLOY.md](DEPLOY.md)**

## 项目结构

```
src/w1_lab/
  api.py          HTTP 层：路由 / 鉴权 / 状态码 / 缓存
  parser.py       纯业务：解析日志行 + 格式校验
  models.py       pydantic 契约（最底层）
  auth.py         pbkdf2 密码哈希 + JWT 签发验证
  db.py           SQLAlchemy 模型 / Engine / Session
  cache.py        缓存读写 + TTL 抖动
migrations/       alembic 迁移链
nginx/            反向代理配置（certs 不进仓库）
tests/            30 个测试
```

## 已知限制

- 自签证书只能本地用，浏览器会警告
- `/debug/whoami` 默认**不注册**（需 `DEBUG=true` 才启用），nginx 也返回 404，双重屏蔽
- 数据库密码是开发用的硬编码值，生产需改用 secret
- **`config.py` / `decorators.py` / `reader.py` 是 W1 的练习产物，未接入主链路**
  （各自文件头写明了定位与去留；其中 `retry` 和 `iter_lines` 会在项目 1 复用）
- 分页、批量导入、日志格式自动识别都还没做
