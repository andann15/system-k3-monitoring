FROM python:3.10-slim

WORKDIR /app

# Install system deps untuk OpenCV
# libgl1-mesa-glx \
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app/dashboard.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
