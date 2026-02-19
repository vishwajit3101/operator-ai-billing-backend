# recreate_aws_table.py – run this once

from app.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Drop old table if it exists (only if you don't care about old data!)
cur.execute("DROP TABLE IF EXISTS aws_spend;")

# Create correct table
cur.execute("""
CREATE TABLE aws_spend (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    service VARCHAR(50) NOT NULL,
    amount NUMERIC NOT NULL
);
""")

conn.commit()
cur.close()
conn.close()

print("SUCCESS: aws_spend table recreated with columns: id, date, service, amount")