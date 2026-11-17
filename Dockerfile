# -----------构建阶段--------------
#AS builder 的作用：后面第二阶段可以用 COPY --from=builder ... 引用这一阶段的文件。
FROM python:3.12-slim AS builder     
#让 uv 用复制而非硬链接方式安装包，避免 Docker 分层文件系统下的硬链接问题。
ENV UV_LINK_MOOD=copy   
 #--no-cache-dir：不保留 pip 缓存，减小中间层体积。
RUN pip install --no-cache-dir uv  

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

#-------------运行阶段---------
FROM python:3.12-slim
# PYTHONDONTWRITEBYTECODE=1：不生成 .pyc 字节码文件，保持镜像干净。
 # PYTHONUNBUFFERED=1：Python 输出不缓冲，日志实时打印到 docker logs（生产必备）。
ENV PYTHONDONTWRITEBYTECODE=1 \ 
    PYTHONUNBUFFERED=1       

WORKDIR /app      
#从 builder 阶段拷贝虚拟环境到最终镜像的 /app/.venv。
COPY --from=builder /app/.venv /app/.venv   
COPY --from=builder /app/src /app/src
COPY alembic.ini ./
COPY migrations ./migrations

ENV PATH="/app/.venv/bin:$PATH"    

EXPOSE 8000       
CMD ["uvicorn", "w1_lab.api:app", "--host", "0.0.0.0", "--port", "8000"]    
