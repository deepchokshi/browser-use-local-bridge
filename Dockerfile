# Browser-Use Local Bridge Docker Image
# Production-ready containerization with browser support

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for browser automation
RUN apt-get update && apt-get install -y \
    # Essential tools
    curl \
    wget \
    gnupg \
    unzip \
    # Browser dependencies
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    # Additional dependencies
    fonts-liberation \
    libappindicator3-1 \
    libxshmfence1 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r browseruser && useradd -r -g browseruser -G audio,video browseruser \
    && mkdir -p /home/browseruser/Downloads \
    && chown -R browseruser:browseruser /home/browseruser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/media /app/browser_data /app/logs \
    && chown -R browseruser:browseruser /app

# Switch to non-root user
USER browseruser

# Set Chrome path for the application
ENV CHROME_EXECUTABLE_PATH=/usr/bin/google-chrome-stable \
    BROWSER_HEADLESS=true \
    MEDIA_DIR=/app/media \
    BROWSER_USER_DATA_DIR=/app/browser_data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"] 