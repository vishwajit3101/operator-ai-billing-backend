def get_mock_tools():
    return [
        {"name": "Anthropic", "credits_remaining": 42350, "percent_remaining": 85.5, "daily_avg_usage": 15420, "status": "warning"},
        {"name": "Tavily", "credits_remaining": 2800, "percent_remaining": 28, "daily_avg_usage": 1200, "status": "critical"},
        # add FullEnrich, Buyercaddy, PostHog as in screenshot
    ]

def get_mock_aws():
    return {
        "monthly_spend": 14100,
        "monthly_budget": 12000,
        "percent_used": 118,
        "services": [{"service": "EC2", "amount": 8200}, {"service": "RDS", "amount": 4500}]
    }