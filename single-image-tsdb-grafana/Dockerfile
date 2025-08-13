# =========================
# Stage 1: Build Python venv with uv
# =========================
FROM ubuntu:24.04 AS builder

ARG QUESTDB_VERSION=9.0.1
ARG GRAFANA_VERSION=12.1.0

# Install only what's necessary for building Python deps
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-venv \
    wget \
 && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Work in /app and create venv
WORKDIR /app
RUN uv venv /app/venv

# Add venv's bin dir to PATH for subsequent commands
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt .
RUN uv pip install -r requirements.txt

# =========================
# Stage 2: Final runtime image
# =========================
FROM ubuntu:24.04

# Build args needed again for this stage
ARG QUESTDB_VERSION=9.0.1
ARG GRAFANA_VERSION=12.1.0
ARG SAMPLE_INTERVAL=15

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    wget \
    openjdk-17-jre-headless \
    python3 \
    curl \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder stage
COPY --from=builder /app/venv /app/venv

# Set PATH so venv Python and uv are default
ENV PATH="/app/venv/bin:$PATH"
ENV SAMPLE_INTERVAL=${SAMPLE_INTERVAL}

# Install QuestDB
RUN mkdir -p /opt/questdb \
    && wget https://github.com/questdb/questdb/releases/download/${QUESTDB_VERSION}/questdb-${QUESTDB_VERSION}-no-jre-bin.tar.gz \
    && tar -xzf questdb-${QUESTDB_VERSION}-no-jre-bin.tar.gz --strip-components=1 -C /opt/questdb \
    && rm questdb-${QUESTDB_VERSION}-no-jre-bin.tar.gz

# Install Grafana
RUN wget -q https://dl.grafana.com/oss/release/grafana_${GRAFANA_VERSION}_amd64.deb \
    && apt-get update \
    && apt-get install -y ./grafana_${GRAFANA_VERSION}_amd64.deb \
    && rm grafana_${GRAFANA_VERSION}_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Install s6-overlay
RUN wget -qO- https://github.com/just-containers/s6-overlay/releases/download/v3.2.1.0/s6-overlay-noarch.tar.xz | tar -Jxpf - -C / && \
    wget -qO- https://github.com/just-containers/s6-overlay/releases/download/v3.2.1.0/s6-overlay-x86_64.tar.xz | tar -Jxpf - -C /

# Copy configs and scripts
WORKDIR /app
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY etc/ /etc/

# Copy Grafana configuration
RUN cp config/grafana.ini /etc/grafana/grafana.ini \
    && mkdir -p /etc/grafana/provisioning/datasources /etc/grafana/provisioning/dashboards \
    && cp config/provisioning/datasources/questdb.yaml /etc/grafana/provisioning/datasources/ \
    && cp config/provisioning/dashboards/dashboards.yaml /etc/grafana/provisioning/dashboards/ \
    && cp config/provisioning/dashboards/*.json /etc/grafana/provisioning/dashboards/

# Create necessary directories
RUN mkdir -p /var/lib/questdb /var/lib/grafana /app/logs \
    && chown -R grafana:grafana /var/lib/grafana \
    && chmod +x scripts/generate_sample_metrics.py

# Create s6-overlay service directories and make scripts executable
RUN mkdir -p /etc/s6-overlay/s6-rc.d/questdb /etc/s6-overlay/s6-rc.d/grafana /etc/s6-overlay/s6-rc.d/sample-metrics /etc/s6-overlay/s6-rc.d/user/contents.d /etc/s6-overlay/s6-rc.d/default/contents.d \
    && chmod +x /etc/s6-overlay/s6-rc.d/questdb/run \
    && chmod +x /etc/s6-overlay/s6-rc.d/questdb/finish \
    && chmod +x /etc/s6-overlay/s6-rc.d/questdb/check \
    && chmod +x /etc/s6-overlay/s6-rc.d/grafana/run \
    && chmod +x /etc/s6-overlay/s6-rc.d/sample-metrics/run

# Expose ports
EXPOSE 3000 9000 8812 9009

# Health check handled by s6-overlay

# Set s6-overlay as entrypoint
ENTRYPOINT ["/init"]