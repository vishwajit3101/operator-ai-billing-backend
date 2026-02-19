from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.database import get_db_connection
from datetime import date, timedelta, datetime
from app.calculations import (
    calculate_exhaustion_date,
    calculate_risk_status,
    generate_alerts
)
from app.posthog import get_real_daily_credit_usage
from app.tavily import get_tavily_remaining_credits
from app.fullenrich import get_fullenrich_remaining_credits
import io
import csv
import boto3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

# Load API keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FULLENRICH_API_KEY = os.getenv("FULLENRICH_API_KEY")
FULLENRICH_USAGE_URL = os.getenv("FULLENRICH_USAGE_URL", "https://api.fullenrich.com/v1/usage")

# Debug prints — AFTER variables are defined
print("[DEBUG] TAVILY_API_KEY loaded:", TAVILY_API_KEY[:10] + "..." if TAVILY_API_KEY else "None")
print("[DEBUG] FULLENRICH_API_KEY loaded:", FULLENRICH_API_KEY[:10] + "..." if FULLENRICH_API_KEY else "None")

def fetch_real_aws_spend(days: int = 30) -> dict:
    try:
        client = boto3.client('ce', region_name=AWS_REGION)
        end = datetime.utcnow().date()
        start = end - timedelta(days=days)
        response = client.get_cost_and_usage(
            TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
            Granularity='MONTHLY',
            Metrics=['AmortizedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        services = []
        total_spend = 0.0
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0].replace('AWS::', '')
                amount = float(group['Metrics']['AmortizedCost']['Amount'])
                services.append({"service": service, "amount": amount})
                total_spend += amount
        print(f"[AWS] Real spend: ${total_spend:.2f}")
        return {"monthly_spend": total_spend, "services": services}
    except Exception as e:
        print(f"[AWS] Error: {str(e)} → mock fallback")
        return {
            "monthly_spend": 14100.0,
            "services": [
                {"service": "EC2", "amount": 8200.0},
                {"service": "RDS", "amount": 4500.0},
                {"service": "Other", "amount": 1400.0}
            ]
        }

def send_alert_email_simulation(alerts: list[dict]):
    critical_alerts = [a for a in alerts if a["severity"] == "critical"]
    if not critical_alerts:
        return

    subject = f"CRITICAL Billing Alert - {len(critical_alerts)} Issues ({date.today().isoformat()})"
    body_lines = [
        "URGENT: Critical billing risks detected",
        "----------------------------------------",
        f"Date: {date.today().isoformat()}",
        f"Total critical alerts: {len(critical_alerts)}",
        "",
    ]

    for alert in critical_alerts:
        body_lines.append(f"[{alert['severity'].upper()}] {alert['message']}")
        body_lines.append(f" → Affected: {alert['affected']}")
        body_lines.append("")

    body_lines.append("Action required immediately to avoid service disruption.")
    body_lines.append("Dashboard: http://your-frontend-url/dashboard")
    body_lines.append("----------------------------------------")

    print("\n" + "="*60)
    print("SIMULATED CRITICAL EMAIL / SLACK")
    print("Subject:", subject)
    print("\n".join(body_lines))
    print("="*60 + "\n")


app = FastAPI(title="Operator.ai Billing Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/dashboard")
async def get_dashboard(days: int = Query(30, ge=1, le=90)):
    conn = get_db_connection()
    cur = conn.cursor()

    start_date = date.today() - timedelta(days=days - 1)

    cur.execute("""
        SELECT name, credits_remaining, percent_remaining, daily_avg_usage
        FROM tools
        WHERE last_updated >= %s
        ORDER BY name
    """, (start_date,))
    tools_rows = cur.fetchall()

    real_daily_usage = get_real_daily_credit_usage(days=7)

    tools = []
    for row in tools_rows:
        name, credits_db, percent, daily_db = row

        # Use real API for Tavily & FullEnrich
        if name == "Tavily":
            credits = get_tavily_remaining_credits()
        elif name == "FullEnrich":
            credits = get_fullenrich_remaining_credits()
        else:
            credits = float(credits_db or 0)

        daily = real_daily_usage.get(name, float(daily_db or 0))
        exhaustion = calculate_exhaustion_date(credits, daily)
        status = calculate_risk_status(float(percent or 0))

        tools.append({
            "name": name,
            "credits_remaining": credits,  # ← this line saves the real value
            "percent_remaining": float(percent or 0),
            "daily_avg_usage": round(daily, 2),
            "predicted_exhaustion": exhaustion,
            "status": status
        })

    aws_data = fetch_real_aws_spend(days=days)

    aws = {
        "monthly_spend": aws_data["monthly_spend"],
        "monthly_budget": 12000.0,
        "percent_used": round((aws_data["monthly_spend"] / 12000.0) * 100, 1) if aws_data["monthly_spend"] > 0 else 0.0,
        "services": aws_data["services"],
        "filtered_days": days
    }

    alerts = generate_alerts(tools, aws)

    cur.close()
    conn.close()

    return {
        "tools": tools,
        "aws": aws,
        "alerts": alerts,
        "alert_count": len(alerts),
        "last_updated": date.today().isoformat(),
        "filtered_days": days,
        "date_range": {
            "from": start_date.isoformat(),
            "to": date.today().isoformat()
        }
    }


@app.get("/alerts")
async def get_alerts(critical_only: bool = False):
    data = get_dashboard(30)
    alerts = data["alerts"]

    if critical_only:
        alerts = [a for a in alerts if a["severity"] == "critical"]

    if any(a["severity"] == "critical" for a in alerts):
        send_alert_email_simulation(alerts)

    return {
        "alerts": alerts,
        "count": len(alerts),
        "timestamp": date.today().isoformat()
    }


@app.get("/export")
async def export_report(
    days: int = Query(30, ge=1, le=90),
    format: str = Query("json", pattern="^(json|csv)$")
):
    data = get_dashboard(days)

    if format == "json":
        return data

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Type", "Name/Service", "Credits/Amount", "% Used", "Daily Avg", "Exhaustion Date", "Status"])

    for tool in data["tools"]:
        writer.writerow([
            "Tool",
            tool["name"],
            tool["credits_remaining"],
            f"{tool['percent_remaining']}%",
            tool["daily_avg_usage"],
            tool.get("predicted_exhaustion", ""),
            tool["status"]
        ])

    for service in data["aws"]["services"]:
        writer.writerow([
            "AWS Service",
            service["service"],
            service["amount"],
            "",
            "",
            "",
            ""
        ])

    writer.writerow([])
    writer.writerow(["Summary", "", "", f"AWS: {data['aws']['percent_used']}%", "", "", ""])
    writer.writerow(["Alert Count", data["alert_count"], "", "", "", "", ""])

    writer.writerow([])
    writer.writerow(["Alerts"])
    writer.writerow(["Severity", "Message", "Affected"])
    for alert in data["alerts"]:
        writer.writerow([alert["severity"], alert["message"], alert["affected"]])

    csv_content = output.getvalue()
    filename = f"billing_report_{date.today().isoformat()}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


handler = Mangum(app)