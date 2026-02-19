import psycopg2
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

# Read connection details from .env
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cur = conn.cursor()

# Create the tables (IF NOT EXISTS = safe to run multiple times)
cur.execute("""
CREATE TABLE IF NOT EXISTS tools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    credits_remaining NUMERIC DEFAULT 0,
    percent_remaining FLOAT DEFAULT 0,
    daily_avg_usage NUMERIC DEFAULT 0,
    predicted_exhaustion DATE,
    status VARCHAR(20) DEFAULT 'safe',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS usage_history (
    id SERIAL PRIMARY KEY,
    tool_name VARCHAR(50),
    date DATE,
    credits_consumed NUMERIC,
    events_count INT
);

CREATE TABLE IF NOT EXISTS aws_spend (
    id SERIAL PRIMARY KEY,
    date DATE,
    service VARCHAR(50),
    amount NUMERIC
);
""")

# Save changes to database
conn.commit()

# Clean up
cur.close()
conn.close()

print("✅ Tables created successfully!")