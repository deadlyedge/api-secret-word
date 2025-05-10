FROM python:3.12-slim
LABEL maintainer="xdream oldlu <xdream@gmail.com>"

# RUN apk add --no-cache curl build-essential libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y \
	  curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
	
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 
COPY ./app /app/app

# Expose port for FastAPI
EXPOSE 8001

# 
CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8001"]