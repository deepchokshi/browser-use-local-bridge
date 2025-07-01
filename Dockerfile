# Browser-Use Local Bridge Docker Image
# Production-ready containerization with Playwright browser support

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies for Playwright browsers
RUN apt-get update && apt-get install -y \
    # Essential tools
    curl \
    wget \
    gnupg \
    unzip \
    git \
    # Playwright browser dependencies
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
    libgdk-pixbuf2.0-0 \
    libxfixes3 \
    libxrender1 \
    libcairo-gobject2 \
    libdbus-1-3 \
    libgtk-4-1 \
    # Additional Playwright dependencies
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    libappindicator3-1 \
    libxshmfence1 \
    libgconf-2-4 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3-dev \
    libgdk-pixbuf2.0-dev \
    libgtk-3-dev \
    libxss-dev \
    # Video and audio support
    libasound2-dev \
    libpangocairo-1.0-0 \
    libatk1.0-dev \
    libcairo-gobject2 \
    libgtk-3-dev \
    libgdk-pixbuf2.0-dev \
    # Additional fonts
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    # Cleanup
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

# Install Playwright and browsers as root
RUN playwright install --with-deps chromium \
    && playwright install --with-deps firefox \
    && playwright install --with-deps webkit \
    && playwright --version

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/media /app/browser_data /app/logs /ms-playwright \
    && chown -R browseruser:browseruser /app \
    && chmod -R 755 /ms-playwright

# Switch to non-root user
USER browseruser

# Set Playwright environment variables
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    BROWSER_HEADLESS=true \
    MEDIA_DIR=/app/media \
    BROWSER_USER_DATA_DIR=/app/browser_data \
    BROWSER_TYPE=chromium

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"] 