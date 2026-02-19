# app/aws_cost.py
import boto3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")  # your region, change if needed

def fetch_real_aws_spend(days: int = 30) -> dict:
    """
    Fetch real AWS cost and usage (last 'days' period, grouped by service).
    Returns {
        "monthly_spend": float,
        "services": [{"service": str, "amount": float}]
    }
    Falls back to mock on error.
    """
    try:
        client = boto3.client('ce', region_name=AWS_REGION)

        end = datetime.utcnow().date()
        start = end - timedelta(days=days)

        response = client.get_cost_and_usage(
            TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
            Granularity='DAILY',  # or 'MONTHLY' if preferred
            Metrics=['AmortizedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        services = []
        total_spend = 0.0

        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0].replace('AWS::', '')  # clean name
                amount = float(group['Metrics']['AmortizedCost']['Amount'])
                services.append({"service": service, "amount": amount})
                total_spend += amount

        print(f"[AWS Cost Explorer] Fetched real spend: ${total_spend:.2f} over {days} days")
        return {
            "monthly_spend": total_spend,
            "services": services
        }

    except Exception as e:
        print(f"[AWS Cost Explorer] Error: {str(e)} - falling back to mock")
        # Fallback mock (your original values)
        return {
            "monthly_spend": 14100.0,
            "services": [
                {"service": "EC2", "amount": 8200.0},
                {"service": "RDS", "amount": 4500.0},
                {"service": "Other", "amount": 1400.0}
            ]
        }