import psycopg2
from psycopg2 import sql
import os

# Можно использовать переменные окружения или напрямую вставить данные
DB_NAME = os.getenv("DB_NAME", "your_db_name")
DB_USER = os.getenv("DB_USER", "your_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password")
DB_HOST = os.getenv("DB_HOST", "your_host")
DB_PORT = os.getenv("DB_PORT", "your_port")

def get_connection():
    return psycopg2.connect(
        dbname="railway",
        user="postgres",
        password="jbbKtpqwIKfhMtTwObttBuKHJTjFxxRU",
        host="caboose.proxy.rlwy.net",
        port="40378"
    )


def create_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username TEXT,
            query TEXT NOT NULL,
            response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

