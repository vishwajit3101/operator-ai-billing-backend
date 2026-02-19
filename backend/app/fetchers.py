# app/fetchers.py
import boto3
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_aws_spend(days_back=30):
    """
    Fetch real AWS cost (monthly grouped by service)
    Requires AWS credentials with Cost Explorer permission
    """
    client = boto3.client('ce', region_name=os.getenv('AWS_REGION', 'us-east-1'))
    
    end = datetime.utcnow().date()
    start = end - timedelta(days=days_back)
    
    response = client.get_cost_and_usage(
        TimePeriod={'Start': start.isoformat(), 'End': end.isoformat()},
        Granularity='MONTHLY',
        Metrics=['AmortizedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )
    
    results = []
    for group in response['ResultsByTime']:
        for item in group['Groups']:
            service = item['Keys'][0].replace('AWS::', '')  # clean name
            amount = float(item['Metrics']['AmortizedCost']['Amount'])
            results.append({'service': service, 'amount': amount})
    
    total = sum(r['amount'] for r in results)
    return {'monthly_spend': total, 'services': results}


def fetch_tavily_credits():
    """
    Get remaining credits from Tavily /usage endpoint
    Returns: float (credits left)
    """
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        print("Warning: TAVILY_API_KEY missing → using mock")
        return 2800.0  # fallback mock

    url = "https://api.tavily.com/usage"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # Tavily returns total usage; assume you know your monthly limit
        # For free tier → 1000 credits/month, but better to track used vs limit
        used = data.get('search_usage', 0) + data.get('research_usage', 0)
        limit = 1000  # change to your actual plan limit
        remaining = limit - used
        
        return float(remaining)
    except Exception as e:
        print(f"Tavily fetch error: {e}")
        return 2800.0  # fallback


def get_posthog_daily_events(event_name, days=1):
    """
    Count events in last N days using HogQL query
    Returns: int (event count)
    """
    project_id = os.getenv('POSTHOG_PROJECT_ID')
    api_key   = os.getenv('POSTHOG_API_KEY')
    host      = os.getenv('POSTHOG_HOST', 'https://us.i.posthog.com')
    
    if not project_id or not api_key:
        print("Warning: PostHog keys missing → mock count")
        return 500 if event_name == 'search_performed' else 100

    url = f"{host}/api/projects/{project_id}/query/"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # HogQL query – count events in last 'days' days
    query_str = f"""
    SELECT count() as cnt
    FROM events
    WHERE event = '{event_name}'
      AND timestamp >= now() - INTERVAL '{days} DAY'
    """
    
    payload = {
        "query": {
            "kind": "HogQLQuery",
            "query": query_str
        }
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        count = result.get('results', [[0]])[0][0]
        return int(count)
    except Exception as e:
        print(f"PostHog query error for {event_name}: {e}")
        return 500 if event_name == 'search_performed' else 100


# ──────────────────────────────────────────────
# Helper: Get daily credit usage for one tool (based on PRD mapping)
# ──────────────────────────────────────────────
EVENT_TO_CREDIT_MAP = {
    'search_performed':   ('Tavily',       1),
    'lead_enriched':      ('FullEnrich',   2),
    'ai_workflow_run':    ('Anthropic',    5),
    'data_fetched':       ('Buyercaddy',   1),
    # add more when needed
}

def get_daily_credit_usage_for_tool(tool_name, days=7):
    total_credits = 0
    for event, (t, credits_per) in EVENT_TO_CREDIT_MAP.items():
        if t == tool_name:
            count = get_posthog_daily_events(event, days=days)
            total_credits += count * credits_per
    return total_credits / days   # average daily