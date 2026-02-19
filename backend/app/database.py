# app/database.py
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD")
        )
        conn.autocommit = False  # we'll commit manually
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise