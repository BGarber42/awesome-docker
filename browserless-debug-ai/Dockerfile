FROM node:22-slim

# Install essential system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Configure npm for faster installs
RUN npm config set fetch-retries 3 \
    && npm config set fetch-retry-mintimeout 5000 \
    && npm config set fetch-retry-maxtimeout 60000 \
    && npm config set maxsockets 50 \
    && npm config set progress false

# Copy package files
COPY package*.json ./

# Install Node.js dependencies with optimizations
RUN npm install --omit=dev --no-audit --no-fund --prefer-offline --progress=false

# Install Playwright browsers with system dependencies
RUN npx playwright install chromium firefox --with-deps \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY app/ ./app/

# Create necessary directories
RUN mkdir -p /app/reports /app/screenshots

# Expose ports
EXPOSE 3000 9222 9223

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start the application
CMD ["node", "app/main.js"]
