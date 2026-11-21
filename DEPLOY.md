# 从零部署 w1-lab

> 目标：一台装了 Docker 的机器，照着本文能在 15 分钟内把服务跑起来。
> 已在 **Windows 11 + Docker Desktop 29.9.2** 上完整验证。

## 0. 这套东西是什么

四个容器，请求链路：

```
浏览器 → nginx:443 → api:8000 → db:5432 / redis:6379
```

| 容器 | 镜像 | 作用 | 宿主机端口 |
|---|---|---|---|
| `nginx` | nginx:1.27-alpine | TLS 终止 + 反向代理（**唯一入口**） | 80 / 443 |
| `api` | 本地构建 | FastAPI 应用 | 无（仅内网 8000） |
| `db` | postgres:16 | 数据持久化 | 无（仅内网 5432） |
| `redis` | redis:7-alpine | 缓存 | 无（仅内网 6379） |

**只有 nginx 对外。** 另外三个只在内网可达——这是有意的安全边界。

## 1. 前置条件

| 软件 | 版本 | 检查命令 | 期望输出 |
|---|---|---|---|
| Docker Desktop | 24+ | `docker info --format "{{.ServerVersion}}"` | 打印出版本号 |
| uv | 0.13+ | `uv --version` | `uv 0.13.x` |
| Git | 2.40+ | `git --version` | `git version 2.4x` |
| openssl | 任意 | `openssl version` | `OpenSSL 3.x` |

> **Windows 用户注意**：拉取基础镜像需要能访问 Docker Hub。
> 如果 `docker pull` 卡住或超时，需要开代理（本项目开发时用 Clash，端口 7897），
> 并在 Docker Desktop 的 Settings → Resources → Proxies 里把 HTTP/HTTPS 都指向
> `http://127.0.0.1:7897`。
>
> **一个坑**：`docker build` 用的构建器和 daemon 是两套进程，**不共享代理配置**。
> 所以建议先把基础镜像 `docker pull` 到本地，再用 `docker build --pull=false` 构建。

## 2. 获取代码

```powershell
git clone https://github.com/cxgmjsws19-lab/w1-lab.git
cd w1-lab
```

## 3. 首次配置

**唯一需要改的地方是数据库密码。**

`docker-compose.yml` 里目前写的是：

```yaml
    environment:
      POSTGRES_PASSWORD: devpass
```

⚠️ **这是开发用的硬编码密码，上生产必须改**，并且要同时改两处：

- `db` 服务的 `POSTGRES_PASSWORD`
- `api` 服务的 `DATABASE_URL` 里的密码部分

**生产做法**：用 Docker secret 或环境变量注入，不要写进 compose 文件。

其余配置都开箱可用，不需要改。

## 4. 生成 TLS 证书

```powershell
New-Item -ItemType Directory -Force -Path nginx/certs | Out-Null
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout nginx/certs/server.key `
  -out nginx/certs/server.crt `
  -subj "/C=CN/O=w1-lab/CN=localhost" `
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

生成的文件：

| 文件 | 是什么 |
|---|---|
| `nginx/certs/server.crt` | 证书（可公开） |
| `nginx/certs/server.key` | **私钥（绝不能提交）** |

**为什么 certs 目录不进仓库**：`server.key` 是私钥。提交到 GitHub 等于公开你的 TLS 身份。
所以 `.gitignore` 里有：

```
nginx/certs/*.key
nginx/certs/*.crt
```

**证书是自签的**，所以浏览器打开 `https://localhost` 会警告「不安全」。**这是预期的**，
点「高级 → 继续访问」即可。要消除警告需要正式 CA 签发的证书（如 Let's Encrypt），那需要真实域名。

**验证证书生成成功**：

```powershell
openssl x509 -in nginx/certs/server.crt -noout -subject -issuer
```

期望看到 `subject=...CN=localhost` 且 `issuer=...CN=localhost`（**自签 = 签发者是自己**）。

## 5. 启动服务

```powershell
docker compose up -d
docker compose ps
```

**期望：四个服务全部 `Up (healthy)`**

```
w1-lab-api-1    Up ... (healthy)    8000/tcp
w1-lab-db-1     Up ... (healthy)    5432/tcp
w1-lab-nginx-1  Up ... (healthy)    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
w1-lab-redis-1  Up ... (healthy)    6379/tcp
```

⚠️ **紧跟 `up -d` 立刻执行 `ps` 时，`nginx` 往往显示 `(health: starting)` 而不是 `(healthy)`。**
这是正常的——它的健康检查间隔是 5 秒，需要跑满一轮才会转成 `(healthy)`，**等 15 秒再查一次**即可。
（实测：刚重启 1 秒时是 `Up 1 second (health: starting)`，13 秒后是 `(healthy)`。）

**启动耗时取决于基础镜像是否已缓存**：

| 情况 | 大约耗时 |
|---|---|
| 四个基础镜像已在本地 + api 镜像层有缓存 | **约 12 秒** |
| 首次运行，需拉 `python:3.12-slim` / `postgres:16` / `nginx:1.27-alpine` / `redis:7-alpine` | **2–5 分钟**（取决于网速） |
| 改了 `src/` 里的代码，需要重建 api 镜像 | 多 6–12 秒 |

**顺利启动的标志**是 `up -d` 的输出里有 `Waiting → Healthy` 的过程，
因为 `api` 的 `depends_on` 配了 `condition: service_healthy`——它会等 db 和 redis 真的就绪才启动。

**如果有服务不是 healthy**：

```powershell
docker compose ps -a                          # -a 才能看到已退出的容器
docker compose logs <服务名> --tail 50
```

## 6. 初始化数据库（最容易错的一步）

**不要在本机直接跑 `alembic upgrade head`。** 会失败：

```
sqlalchemy.exc.OperationalError: (psycopg.errors.ConnectionTimeout) connection timeout expired
```

原因：`db` 服务**不映射端口到宿主机**，本机的 `127.0.0.1:5432` 连不上。
这是有意设计的——数据库不该暴露在宿主机。

### 正确做法

```powershell
docker compose run --rm -v "./migrations:/app/migrations" api alembic upgrade head
```

期望输出——**全新数据库会依次执行 6 个迁移**（你看到的行数应该正好是 6 个 `Running upgrade`）：

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, baseline: create log_entries
INFO  [alembic.runtime.migration] Running upgrade 0001 -> 2b97c108be09, add user_agent
INFO  [alembic.runtime.migration] Running upgrade 2b97c108be09 -> df591daed71a, add users table
INFO  [alembic.runtime.migration] Running upgrade df591daed71a -> 0ba052a31a3c, add password_hash to users
INFO  [alembic.runtime.migration] Running upgrade 0ba052a31a3c -> 8632e1838170, add index on log_entries.ip
INFO  [alembic.runtime.migration] Running upgrade 8632e1838170 -> d42634b6cff3, change ts to timestamptz
```

**如果行数少于 6 行**，说明数据库里已经有部分迁移记录（不是全新库），
先确认 `alembic_version` 里的值再继续，别硬跑。

### 两个参数为什么必须有

| 参数 | 不加会怎样 |
|---|---|
| `--rm` | 容器跑完留在那儿，攒一堆一次性容器 |
| `-v "./migrations:/app/migrations"` | 如果**生成**迁移，文件会留在容器里，容器一删就没了 |

⚠️ **重要**：镜像里也有一份 `migrations/`（构建时 `COPY` 进去的）。
**只要你在宿主机改过 `migrations/`，就必须加 `-v` 挂载**，否则 alembic 看到的是镜像里的旧迁移链，
表现为「明明加了迁移，`alembic upgrade` 却说已经是最新」——这个坑很难查。

### 验证

```powershell
docker compose exec -T db psql -U postgres -d w1lab -c "SELECT version_num FROM alembic_version;"
```

期望：打印出一个 12 位的版本号。

```powershell
docker compose exec -T db psql -U postgres -d w1lab -c "\dt"
```

期望：至少看到 `log_entries`、`users`、`alembic_version` 三张表。

⚠️ **别用 `/readyz` 判断迁移有没有跑过。** 它的实现只是 `session.execute(text("SELECT 1"))`，
**不碰任何业务表**——所以哪怕一张表都没有，`/readyz` 也返回 200。
（已实测：在一个空数据库上执行 `SELECT 1` 是成功的。）

**判断迁移跑没跑，只能看这两个**：

```powershell
docker compose exec -T db psql -U postgres -d w1lab -c "SELECT version_num FROM alembic_version;"
docker compose exec -T db psql -U postgres -d w1lab -c "\dt"
```

## 7. 验证

按顺序执行，每条都要对上：

```powershell
curl.exe -sk -o NUL -w "health  %{http_code}`n" https://127.0.0.1/health
curl.exe -sk -o NUL -w "readyz  %{http_code}`n" https://127.0.0.1/readyz
curl.exe -sk -o NUL -w "stats   %{http_code}`n" https://127.0.0.1/entries/stats
curl.exe -sk -o NUL -w "debug   %{http_code}`n" https://127.0.0.1/debug/whoami
curl.exe -s  -o NUL -w "http80  %{http_code}`n" http://127.0.0.1/entries/stats
```

**期望**：

| 端点 | 期望 | 说明 |
|---|---|---|
| `/health` | `200` | 进程存活 |
| `/readyz` | `200` | 依赖可用（**真的查了数据库**） |
| `/entries/stats` | `200` | 业务接口 |
| `/debug/whoami` | `404` | **被 nginx 屏蔽了**，这是对的 |
| `http://` 那条 | `301` | HTTP 强制跳 HTTPS |

### 最有说服力的一条：证明健康检查是真的

```powershell
docker compose stop db
curl.exe -sk -o NUL -w "readyz  %{http_code}`n" https://127.0.0.1/readyz
curl.exe -sk -o NUL -w "health  %{http_code}`n" https://127.0.0.1/health
docker compose start db
```

**期望**：

```
readyz  503      ← 依赖不可用，如实报告
health  200      ← 只看进程，进程确实活着
```

**这两个数字的差异就是「分层健康检查」的意义**：
`/health` 回答「进程还在吗」（挂了该重启），`/readyz` 回答「能对外服务吗」（挂了摘流量）。
如果把两者混成一个，数据库抖动就会导致所有实例被误判为死亡并重启。

## 8. 常见故障

### 8.1 `docker compose up -d` 说 Started，但 `ps` 里没有这个服务

**症状**：`up` 的输出显示 `✔ Container xxx Started`，但 `docker compose ps` 看不到它。

**原因**：容器启动后立刻崩溃退出。`up -d` 只保证容器被创建，不保证它活着。

**解决**：

```powershell
docker compose ps -a                          # 加 -a 才看得到已退出的
docker compose logs <服务名> --tail 30
```

常见根因：配置语法错（nginx）、环境变量缺、端口被占。

### 8.2 改了 `nginx/nginx.conf` 但行为没变

**原因**：配置文件是 bind-mount，**文件本身是实时的**，但 nginx 进程在启动时把配置读进了内存，
之后不再看磁盘。**改文件 ≠ 生效。**

**解决**：

```powershell
docker compose exec -T nginx nginx -t         # 先校验语法
docker compose exec -T nginx nginx -s reload  # 平滑重载，不中断服务
```

⚠️ **reload 失败时 nginx 会保持旧配置继续服务**，错误不明显。**所以必须回读验证行为**，
不能只看 reload 命令有没有报错。

### 8.3 改了代码但容器里跑的还是旧的

**原因**：镜像里的代码是 `COPY src ./src` 烤进去的，**不是挂载的**。
只看 `up -d` 不会重建镜像。

**解决**：

```powershell
docker compose build api     # 确认输出有 FINISHED 且无 ERROR
docker compose up -d api
```

**验证镜像里真的是新代码**（下面这条命令会打印出模型里 `ts` 列的时区设置，
如果输出 `timezone=True` 说明镜像里是 2026-11-20 之后的代码）：

```powershell
docker compose run --rm --no-deps api python -c "from w1_lab.db import LogEntryRow as T; print('timezone =', getattr(T.__table__.c.ts.type, 'timezone', 'N/A'))"
```

⚠️ **不要用 `python -c "import w1_lab; print(w1_lab.__file__)"` 做这个验证**——
它只会打印 `/app/src/w1_lab/__init__.py`，**无论代码新旧都一样**，证明不了任何事。

## 9. 上线前必做

- [ ] **改掉默认数据库密码**（`devpass`），并用 secret 注入而不是写进 compose
- [ ] **删掉 `/debug/whoami` 或加鉴权**——它会回显内网 IP 和代理链，是信息泄露
      （目前 nginx 已返回 404 屏蔽，但应用层路由仍存在，内网可直接访问）
- [ ] **换成正式证书**（Let's Encrypt / 云厂商证书），自签证书只能本地用
- [ ] **收紧防火墙**：只放行 80/443，且只对需要的网络配置开放
      （本项目已配 `w1-lab HTTP/HTTPS` 仅 Private/Domain，另加一条 `w1-lab BLOCK public` 挡公共网络）
- [ ] **配日志轮转上限**：目前是 `json-file` + `10m × 3`，确认符合容量规划
- [ ] **确认缓存故障会降级**：Redis 挂掉时接口应查库而不是直接 500
- [ ] **给数据库配定期备份**（`pg_dump` + 定时任务）

## 10. 彻底重来

如果环境搞乱了，想从零开始：

```powershell
docker compose down -v      # ⚠️ -v 会删除 pgdata 卷，数据库数据全部丢失
docker compose up -d
docker compose run --rm -v "./migrations:/app/migrations" api alembic upgrade head
```

`nginx/certs/` 是宿主机目录，不受 `down -v` 影响，证书还在。
