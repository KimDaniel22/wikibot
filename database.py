import psycopg2

def get_connection():
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='54321',
        host='localhost',
        port='5432'
    )
    conn.set_client_encoding('UTF8')
    return conn

def clean_text(text):
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    return str(text).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")