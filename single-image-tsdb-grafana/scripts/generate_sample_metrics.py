#!/usr/bin/env python3
"""
Sample metrics generator for QuestDB
Generates realistic system and application metrics
"""

import time
import random
import requests
import os
import sys
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
QUESTDB_URL = "http://localhost:9000"
SAMPLE_INTERVAL = int(os.getenv('SAMPLE_INTERVAL', '15'))  # seconds
ENABLE_SAMPLE_METRICS = os.getenv('SAMPLE_METRICS', 'true').lower() == 'true'

# Metric dimensions (expand fan-out)
HOSTS = [f"server{i}" for i in range(1, 11)]
DEVICES = ["sda1", "sda2", "sdb1", "sdb2", "nvme0n1", "nvme0n2"]
INTERFACES = ["eth0", "eth1", "eth2", "lo"]
SERVICES = ["api", "web", "database", "auth", "cache"]
ENDPOINTS = [
    "/health",
    "/users",
    "/orders",
    "/products",
    "/login",
    "/logout",
    "/inventory",
]

# Create a session with connection pooling
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)

def wait_for_questdb():
    """Wait for QuestDB to be ready"""
    max_retries = 30
    for attempt in range(max_retries):
        try:
            response = session.get(f"{QUESTDB_URL}/exec?query=SELECT%201", timeout=5)
            if response.status_code == 200:
                print("QuestDB is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Waiting for QuestDB... ({attempt + 1}/{max_retries})")
        time.sleep(2)
    
    print("QuestDB not available, skipping sample metrics")
    return False

def create_tables():
    """Create sample tables in QuestDB"""
    tables = [
        "CREATE TABLE IF NOT EXISTS cpu_usage (timestamp TIMESTAMP, host SYMBOL, value DOUBLE) timestamp(timestamp) WAL;",
        "CREATE TABLE IF NOT EXISTS memory_usage (timestamp TIMESTAMP, host SYMBOL, value DOUBLE) timestamp(timestamp) WAL;",
        "CREATE TABLE IF NOT EXISTS disk_usage (timestamp TIMESTAMP, host SYMBOL, device SYMBOL, value DOUBLE) timestamp(timestamp) WAL;",
        "CREATE TABLE IF NOT EXISTS network_traffic (timestamp TIMESTAMP, host SYMBOL, interface SYMBOL, bytes_in DOUBLE, bytes_out DOUBLE) timestamp(timestamp) WAL;",
        "CREATE TABLE IF NOT EXISTS application_metrics (timestamp TIMESTAMP, service SYMBOL, endpoint SYMBOL, response_time DOUBLE, status_code LONG) timestamp(timestamp) WAL;"
    ]
    
    for table_sql in tables:
        try:
            response = session.get(f"{QUESTDB_URL}/exec?query={table_sql}")
            if response.status_code == 200:
                print(f"Created table: {table_sql.split('(')[0].split()[-1]}")
        except Exception as e:
            print(f"Error creating table: {e}")

def generate_cpu_metrics():
    """Generate CPU usage metrics"""
    hosts = HOSTS
    base_usage = random.uniform(20, 40)
    variation = random.uniform(-10, 10)
    usage = max(0, min(100, base_usage + variation))
    
    for host in hosts:
        host_usage = max(0, min(100, usage + random.uniform(-5, 5)))
        timestamp = time.time_ns()
        data = f"cpu_usage,host={host} value={host_usage:.2f} {timestamp}"
        
        try:
            response = session.post(f"{QUESTDB_URL}/write", data=data, headers={'Content-Type': 'text/plain'}, timeout=5)
            if response.status_code != 204:
                print(f"Error writing CPU metrics: {response.status_code}")
        except Exception as e:
            print(f"Error writing CPU metrics: {e}")

def generate_memory_metrics():
    """Generate memory usage metrics"""
    hosts = HOSTS
    base_usage = random.uniform(50, 80)
    variation = random.uniform(-15, 15)
    usage = max(0, min(100, base_usage + variation))
    
    for host in hosts:
        host_usage = max(0, min(100, usage + random.uniform(-10, 10)))
        timestamp = time.time_ns()
        data = f"memory_usage,host={host} value={host_usage:.2f} {timestamp}"
        
        try:
            response = session.post(f"{QUESTDB_URL}/write", data=data, headers={'Content-Type': 'text/plain'}, timeout=5)
            if response.status_code != 204:
                print(f"Error writing memory metrics: {response.status_code}")
        except Exception as e:
            print(f"Error writing memory metrics: {e}")

def generate_disk_metrics():
    """Generate disk usage metrics"""
    hosts = HOSTS
    devices = DEVICES
    base_usage = random.uniform(30, 70)
    
    for host in hosts:
        for device in devices:
            usage = max(0, min(100, base_usage + random.uniform(-20, 20)))
            timestamp = time.time_ns()
            data = f"disk_usage,host={host},device={device} value={usage:.2f} {timestamp}"
            
            try:
                response = session.post(f"{QUESTDB_URL}/write", data=data, headers={'Content-Type': 'text/plain'}, timeout=5)
                if response.status_code != 204:
                    print(f"Error writing disk metrics: {response.status_code}")
            except Exception as e:
                print(f"Error writing disk metrics: {e}")

def generate_network_metrics():
    """Generate network traffic metrics"""
    hosts = HOSTS
    interfaces = INTERFACES
    
    for host in hosts:
        for interface in interfaces:
            bytes_in = random.uniform(1000, 10000)
            bytes_out = random.uniform(500, 5000)
            timestamp = time.time_ns()
            data = f"network_traffic,host={host},interface={interface} bytes_in={bytes_in:.2f},bytes_out={bytes_out:.2f} {timestamp}"
            
            try:
                response = session.post(f"{QUESTDB_URL}/write", data=data, headers={'Content-Type': 'text/plain'}, timeout=5)
                if response.status_code != 204:
                    print(f"Error writing network metrics: {response.status_code}")
            except Exception as e:
                print(f"Error writing network metrics: {e}")

def generate_application_metrics():
    """Generate application performance metrics"""
    services = SERVICES
    endpoints = ENDPOINTS
    status_codes = [200, 200, 200, 200, 404, 500]  # Mostly successful, some errors
    
    for service in services:
        for endpoint in endpoints:
            response_time = random.uniform(10, 500)
            status_code = random.choice(status_codes)
            timestamp = time.time_ns()
            data = f"application_metrics,service={service},endpoint={endpoint} response_time={response_time:.2f},status_code={status_code} {timestamp}"
            
            try:
                response = session.post(f"{QUESTDB_URL}/write", data=data, headers={'Content-Type': 'text/plain'}, timeout=5)
                if response.status_code != 204:
                    print(f"Error writing application metrics: {response.status_code}")
            except Exception as e:
                print(f"Error writing application metrics: {e}")

def main():
    """Main function to generate sample metrics"""
    if not ENABLE_SAMPLE_METRICS:
        print("Sample metrics disabled")
        return
    
    print("Starting sample metrics generator...")
    
    # Wait for QuestDB to be ready
    if not wait_for_questdb():
        return
    
    # Create tables
    create_tables()
    
    # Generate metrics continuously
    while True:
        try:
            generate_cpu_metrics()
            generate_memory_metrics()
            generate_disk_metrics()
            generate_network_metrics()
            generate_application_metrics()
            
            print(f"Generated metrics at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(SAMPLE_INTERVAL)
            
        except KeyboardInterrupt:
            print("Stopping sample metrics generator...")
            break
        except Exception as e:
            print(f"Error generating metrics: {e}")
            time.sleep(SAMPLE_INTERVAL)

if __name__ == "__main__":
    main()
