# app/mock_data.py
from datetime import date, timedelta

def generate_mock_tools():
    today = date.today()
    return [
        {
            "name": "Anthropic",
            "credits_remaining": 42350.0,
            "percent_remaining": 85.5,
            "daily_avg_usage": 15420.0,
            "predicted_exhaustion": (today + timedelta(days=3)).isoformat(),
            "status": "warning",
            "last_updated": today.isoformat()
        },
        {
            "name": "Tavily",
            "credits_remaining": 2800.0,
            "percent_remaining": 28.0,
            "daily_avg_usage": 1200.0,
            "predicted_exhaustion": (today + timedelta(days=2)).isoformat(),
            "status": "critical",
            "last_updated": today.isoformat()
        },
        {
            "name": "FullEnrich",
            "credits_remaining": 500.0,
            "percent_remaining": 10.0,
            "daily_avg_usage": 80.0,
            "predicted_exhaustion": (today + timedelta(days=6)).isoformat(),
            "status": "critical",
            "last_updated": today.isoformat()
        },
        {
            "name": "Buyercaddy",
            "credits_remaining": 6800.0,
            "percent_remaining": 85.0,
            "daily_avg_usage": 400.0,
            "predicted_exhaustion": (today + timedelta(days=17)).isoformat(),
            "status": "safe",
            "last_updated": today.isoformat()
        }
    ]

def generate_mock_aws_services():
    return [
        {"service": "EC2", "amount": 8200.0},
        {"service": "RDS", "amount": 4500.0},
        {"service": "Other", "amount": 1400.0}
    ]