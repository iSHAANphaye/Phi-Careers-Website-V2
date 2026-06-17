import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure database connection parameters
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3307")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "phi_careers")
}

# Create a connection pool
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="phi_careers_pool",
        pool_size=5,
        pool_reset_session=True,
        **db_config
    )
except mysql.connector.Error as err:
    print(f"Error creating connection pool: {err}")
    connection_pool = None

def get_connection():
    """Returns a connection from the pool or creates a new one."""
    if connection_pool:
        return connection_pool.get_connection()
    return mysql.connector.connect(**db_config)

def execute_query(query, params=None):
    """Executes a query (INSERT, UPDATE, DELETE) using parameterized parameters.
    Returns the last inserted row ID for INSERTs, or rowcount for updates/deletes."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        rowcount = cursor.rowcount
        return last_id if last_id else rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def fetch_all(query, params=None):
    """Fetches all rows for a query and returns a list of dictionaries."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def fetch_one(query, params=None):
    """Fetches a single row for a query and returns a dictionary, or None."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
