# Use NVIDIA CUDA runtime (smaller than -devel)
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for dlib
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip python3.10-dev \
    ffmpeg libsm6 libxext6 curl \
    cmake build-essential \
    libboost-all-dev libgtk2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies first (optimize caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application files
COPY . /app/

# Expose port 8080 for ECS
EXPOSE 8000

# Start FastAPI server using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
