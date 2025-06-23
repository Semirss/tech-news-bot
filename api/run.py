from daily_tech_bot import main as run_bot

def handler(request):
    run_bot()
    return {
        "statusCode": 200,
        "body": "✅ Bot ran successfully from Vercel!"
    }
