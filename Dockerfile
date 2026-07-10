FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -m pip install --no-cache-dir -e .

EXPOSE 8090
CMD ["python", "-m", "uvicorn", "corp_kb.app:app", "--host", "0.0.0.0", "--port", "8090"]
