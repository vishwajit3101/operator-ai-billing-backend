# lambda_handler.py - hourly job

import json
import os
import psycopg
import boto3
from datetime import date, timedelta


def get_db_connection():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
    )


def lambda_handler(event, context):
    print("Hourly fetch started...")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        today = date.today()

        # AWS Cost Explorer
        ce = boto3.client("ce")
        end = today
        start = end - timedelta(days=30)

        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="MONTHLY",
            Metrics=["AmortizedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        total = 0.0
        services = []

        for r in resp["ResultsByTime"]:
            for g in r["Groups"]:
                svc = g["Keys"][0].replace("AWS::", "")
                amt = float(g["Metrics"]["AmortizedCost"]["Amount"])
                services.append({"service": svc, "amount": amt})
                total += amt

        print(f"Fetched real AWS spend: ${total:.2f}")

        # Update RDS
        for s in services:
            cur.execute(
                """
                INSERT INTO aws_spend (date, service, amount)
                VALUES (%s, %s, %s)
                ON CONFLICT (date, service)
                DO UPDATE SET amount = EXCLUDED.amount
                """,
                (today, s["service"], s["amount"]),
            )

        conn.commit()
        print("RDS updated successfully")

    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()

    return {"statusCode": 200, "body": json.dumps("Hourly fetch done")}
