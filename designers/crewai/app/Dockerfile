FROM python:3.12-slim
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
COPY . /app
WORKDIR /app
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8321"]
