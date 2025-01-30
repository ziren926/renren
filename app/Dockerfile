# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -U appuser && \
    mkdir -p /app/logs /app/uploads && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 复制依赖文件
COPY --chown=appuser:appuser requirements.txt .

# 安装Python依赖
RUN pip install --user --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# 复制应用程序代码
COPY --chown=appuser:appuser . .

# 暴露端口
EXPOSE 5000

# 将用户本地 bin 目录添加到 PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "run:app"]