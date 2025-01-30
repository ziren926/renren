# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建非 root 用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 复制项目文件
COPY --chown=appuser:appuser . .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask-cors

# 设置 PATH 以包含用户的 .local/bin
ENV PATH="/home/appuser/.local/bin:${PATH}"

# 暴露端口
EXPOSE 5000

# 修改启动命令，增加超时设置和其他参数
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gthread", "--threads", "2", "--timeout", "120", "run:app"] 