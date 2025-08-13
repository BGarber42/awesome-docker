import os
import sqlite3
import pymysql
import psycopg2
from datetime import datetime, timedelta
import random

# Environment variables
DB_TYPE = os.getenv('DB_TYPE', 'mysql')
DB_NAME = os.getenv('DB_NAME', 'testdb')
DB_USER = os.getenv('DB_USER', 'testuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'testpass')

def get_connection():
    """Get database connection based on type"""
    if DB_TYPE == 'mysql':
        return pymysql.connect(
            host='localhost',  # Connect to local MySQL server
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
    elif DB_TYPE == 'postgresql':
        return psycopg2.connect(
            host='localhost',  # Connect to local PostgreSQL server
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    elif DB_TYPE == 'sqlite':
        db_path = f'/app/data/{DB_NAME}.db'
        return sqlite3.connect(db_path)
    else:
        raise ValueError(f"Unsupported database type: {DB_TYPE}")

def get_placeholder():
    """Get the correct placeholder for the database type"""
    if DB_TYPE == 'sqlite':
        return '?'
    else:
        return '%s'

def create_tables(conn):
    """Create sample tables"""
    cursor = conn.cursor()
    
    # Users table
    if DB_TYPE == 'sqlite':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    # Products table
    if DB_TYPE == 'sqlite':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    # Orders table
    if DB_TYPE == 'sqlite':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                total_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                status VARCHAR(20) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
    
    conn.commit()

def seed_users(conn):
    """Seed users table with sample data"""
    cursor = conn.cursor()
    placeholder = get_placeholder()
    
    users = [
        ('john_doe', 'john@example.com', 'admin'),
        ('jane_smith', 'jane@example.com', 'user'),
        ('bob_wilson', 'bob@example.com', 'user'),
        ('alice_brown', 'alice@example.com', 'moderator'),
        ('charlie_davis', 'charlie@example.com', 'user'),
    ]
    
    # Add more random users
    for i in range(45):
        username = f'user_{i+6}'
        email = f'user{i+6}@example.com'
        role = random.choice(['user', 'moderator', 'admin'])
        users.append((username, email, role))
    
    for user in users:
        try:
            cursor.execute(
                f'INSERT INTO users (username, email, role) VALUES ({placeholder}, {placeholder}, {placeholder})',
                user
            )
        except:
            # Ignore duplicate key errors
            pass
    
    conn.commit()

def seed_products(conn):
    """Seed products table with sample data"""
    cursor = conn.cursor()
    placeholder = get_placeholder()
    
    categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports']
    products = [
        ('Laptop Pro', 'Electronics', 1299.99, 50),
        ('Smartphone X', 'Electronics', 799.99, 100),
        ('T-Shirt', 'Clothing', 19.99, 200),
        ('Programming Book', 'Books', 49.99, 75),
        ('Garden Tool Set', 'Home & Garden', 89.99, 30),
        ('Running Shoes', 'Sports', 129.99, 60),
    ]
    
    # Add more random products
    for i in range(94):
        name = f'Product {i+7}'
        category = random.choice(categories)
        price = round(random.uniform(10.0, 1000.0), 2)
        stock = random.randint(10, 200)
        products.append((name, category, price, stock))
    
    for product in products:
        try:
            cursor.execute(
                f'INSERT INTO products (name, category, price, stock) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})',
                product
            )
        except:
            # Ignore duplicate key errors
            pass
    
    conn.commit()

def seed_orders(conn):
    """Seed orders table with sample data"""
    cursor = conn.cursor()
    placeholder = get_placeholder()
    
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    
    # Get user and product IDs
    cursor.execute('SELECT id FROM users LIMIT 10')
    user_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT id, price FROM products LIMIT 20')
    product_data = cursor.fetchall()
    
    orders = []
    for i in range(200):
        user_id = random.choice(user_ids)
        product_id, price = random.choice(product_data)
        quantity = random.randint(1, 5)
        status = random.choice(statuses)
        total_amount = price * quantity
        
        orders.append((user_id, product_id, quantity, status, total_amount))
    
    for order in orders:
        try:
            cursor.execute(
                f'INSERT INTO orders (user_id, product_id, quantity, status, total_amount) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})',
                order
            )
        except:
            # Ignore duplicate key errors
            pass
    
    conn.commit()

def seed_database():
    """Main function to seed the database"""
    print(f"Seeding {DB_TYPE} database...")
    
    # For SQLite, no need to wait for database to be ready
    if DB_TYPE == 'sqlite':
        try:
            conn = get_connection()
            print(f"Connected to {DB_TYPE} database successfully")
        except Exception as e:
            print(f"Failed to connect to SQLite database: {e}")
            raise
    else:
        # Wait for database to be ready (MySQL/PostgreSQL)
        max_retries = 30
        for attempt in range(max_retries):
            try:
                conn = get_connection()
                print(f"Connected to {DB_TYPE} database successfully")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1}/{max_retries}: Database not ready yet, retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    print(f"Failed to connect to database after {max_retries} attempts: {e}")
                    raise
    
    try:
        # Create tables
        create_tables(conn)
        print("Tables created successfully")
        
        # Seed data
        seed_users(conn)
        print("Users seeded successfully")
        
        seed_products(conn)
        print("Products seeded successfully")
        
        seed_orders(conn)
        print("Orders seeded successfully")
        
        print(f"Database seeding completed for {DB_TYPE}")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    seed_database()
