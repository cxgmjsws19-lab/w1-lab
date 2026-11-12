# w1-lab API

Base URL:'http://127.0.0.1:8000'
认证方式:Bearer JWT - 请求头 `Authorization: Bearer <token>`

## 公开接口

### GET/health

- 200：'{"status":"ok"}'

### POST/register

-请求:'{"username":"str","password":"str"}'
-201:'{"access_token":"str","token_type":"bearer"}'
-409:用户名已存在

### POST/login
-请求:'{"username":"str","password":"str"}'
-200:'{"access_token":"str","token_type":"bearer"}
-401:用户名或密码错误

## 需认证接口

请求头必须带 'Authorization:Bearer<token>'

### POST/entries
-请求:'{"line":"一行日志文本，7个空格分隔字段"}'
-201:'LogEntry'对象
-401：缺少/无效/过期token（响应带 `WWW-Authenticate: Bearer`）
-422：日志格式不符合7字段约定

### GET/entries/stats

-200:"{"total":int,"by_status":{"200":int,...}}
-响应头:'X-Cache:HIT|MISS'
-缓存TTL60秒，任何写操作会立即让缓存失效

## 错误响应格式

所有错误统一为'{"detail":"说明文字"}'

## 已知限制

- 无分页（`GET /entries` 列表接口尚未实现）
- 无 RBAC（所有登录用户权限相同）
- JWT 无刷新机制（24 小时后需重新登录）
- 缓存是进程内的（fakeredis 模拟），多进程不共享
