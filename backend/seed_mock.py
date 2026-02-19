# seed_mock.py  (run from backend/ folder)

# seed_mock.py (run from backend/ folder)

from app.database import get_db_connection
from mock_data import generate_mock_tools, generate_mock_aws_services
from datetime import date
conn = get_db_connection()
cur = conn.cursor()

# Clear old data (safe for testing)
cur.execute("DELETE FROM tools")
cur.execute("DELETE FROM aws_spend")

# Insert tools
tools = generate_mock_tools()
for t in tools:
    cur.execute("""
        INSERT INTO tools (
            name, credits_remaining, percent_remaining, daily_avg_usage,
            predicted_exhaustion, status, last_updated
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET
            credits_remaining = EXCLUDED.credits_remaining,
            percent_remaining = EXCLUDED.percent_remaining,
            daily_avg_usage = EXCLUDED.daily_avg_usage,
            predicted_exhaustion = EXCLUDED.predicted_exhaustion,
            status = EXCLUDED.status,
            last_updated = EXCLUDED.last_updated
    """, (
        t["name"], t["credits_remaining"], t["percent_remaining"],
        t["daily_avg_usage"], t["predicted_exhaustion"], t["status"],
        t["last_updated"]
    ))

# Insert AWS spend (one row per service, today's date)
today = date.today()
for s in generate_mock_aws_services():
    cur.execute("""
        INSERT INTO aws_spend (date, service, amount)
        VALUES (%s, %s, %s)
    """, (today, s["service"], s["amount"]))

conn.commit()
cur.close()
conn.close()

print("Mock data seeded successfully into database!")
print(f"Inserted {len(tools)} tools and {len(generate_mock_aws_services())} AWS services.")