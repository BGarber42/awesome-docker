FROM python:3.12-slim

# Build argument for database type (default to 'all' for latest tag)
ARG DB_TYPE=all

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    wget \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install database servers based on DB_TYPE
RUN if [ "$DB_TYPE" = "all" ] || [ "$DB_TYPE" = "mysql" ]; then \
        # Add MySQL repository and install MySQL
        wget https://dev.mysql.com/get/mysql-apt-config_0.8.29-1_all.deb \
        && DEBIAN_FRONTEND=noninteractive dpkg -i mysql-apt-config_0.8.29-1_all.deb \
        && rm mysql-apt-config_0.8.29-1_all.deb \
        && apt-get update \
        && apt-get install -y mysql-server \
        && rm -rf /var/lib/apt/lists/*; \
    fi

RUN if [ "$DB_TYPE" = "all" ] || [ "$DB_TYPE" = "postgresql" ]; then \
        # Add PostgreSQL repository and install PostgreSQL
        sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
        && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
        && apt-get update \
        && apt-get install -y postgresql postgresql-contrib \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/data /var/lib/mysql /var/lib/postgresql

# Expose ports
EXPOSE 8080 8081 3306 5432

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
