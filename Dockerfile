FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir pymodbus pyserial fastapi uvicorn
COPY main.py settings.py ./
CMD ["python", "main.py"]
