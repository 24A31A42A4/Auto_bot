FROM mcr.microsoft.com/playwright/python:v1.39.0-jammy

WORKDIR /app

# Copy all backend files into the current WORKDIR
COPY backend/ .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Playwright browsers are in the right place
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Expose the port (Railway uses PORT env var, but we default to 8080)
EXPOSE 8080

# Command to run the app — use Railway's dynamic PORT or default to 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
