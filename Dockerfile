FROM python:3.12-slim
WORKDIR /app
COPY dist/ dist/
COPY serve.py .
CMD ["python", "serve.py"]
