FROM python:3.10-slim

WORKDIR /app
COPY backend/ .

RUN pip install --no-cache-dir -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH=/pw-browsers
RUN playwright install --with-deps chromium

EXPOSE 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]