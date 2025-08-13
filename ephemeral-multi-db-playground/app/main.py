from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import time
import threading
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import scripts
sys.path.append('/app')

app = Flask(__name__)
CORS(app)

# Global variables
start_time = datetime.now()
ttl_seconds = int(os.getenv('TTL', 3600))
db_type = os.getenv('DB_TYPE', 'mysql')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database_type': db_type,
        'uptime': str(datetime.now() - start_time)
    })

@app.route('/status', methods=['GET'])
def status():
    """Get current status and TTL information"""
    elapsed = datetime.now() - start_time
    remaining = ttl_seconds - elapsed.total_seconds()
    
    return jsonify({
        'database_type': db_type,
        'start_time': start_time.isoformat(),
        'elapsed_seconds': elapsed.total_seconds(),
        'ttl_seconds': ttl_seconds,
        'remaining_seconds': max(0, remaining),
        'status': 'running' if remaining > 0 else 'expired'
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset and reseed the database"""
    try:
        # Import here to avoid circular imports
        from scripts.seed_database import seed_database
        
        # Reset database
        seed_database()
        
        return jsonify({
            'status': 'success',
            'message': 'Database reset and reseeded successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/info', methods=['GET'])
def info():
    """Get database connection information"""
    db_name = os.getenv('DB_NAME', 'testdb')
    db_user = os.getenv('DB_USER', 'testuser')
    db_password = os.getenv('DB_PASSWORD', 'testpass')
    
    connection_info = {
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'database': db_name,
            'user': db_user,
            'password': db_password
        },
        'postgresql': {
            'host': 'localhost',
            'port': 5432,
            'database': db_name,
            'user': db_user,
            'password': db_password
        },
        'sqlite': {
            'database': f'/app/data/{db_name}.db'
        }
    }
    
    return jsonify({
        'database_type': db_type,
        'connection_info': connection_info.get(db_type, {}),
        'sample_tables': ['users', 'products', 'orders']
    })

if __name__ == '__main__':
    port = 8080  # Use consistent port for all database types
    app.run(host='0.0.0.0', port=port, debug=False)
