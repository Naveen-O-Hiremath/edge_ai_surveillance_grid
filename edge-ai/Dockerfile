FROM python:3.12-slim



WORKDIR /app



RUN apt-get update && apt-get install -y --no-install-recommends \

    libgl1 libglib2.0-0 curl \

    && rm -rf /var/lib/apt/lists/*



COPY requirements.txt .



# CPU-only PyTorch + ultralytics for real YOLO detection

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \

    && pip install --no-cache-dir -r requirements.txt



COPY . .



RUN mkdir -p /app/data/evidence /app/data/baselines /app/models \

    && python -c "from ultralytics import YOLO; m=YOLO('yolov8n.pt'); import shutil, os; shutil.copy('yolov8n.pt', '/app/models/yolov8n.pt') if os.path.exists('yolov8n.pt') else None"



EXPOSE 8001



CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]


