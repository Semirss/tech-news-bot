from daily_tech_bot import main as run_bot

def handler(request):
    try:
        run_bot()
        return {"statusCode": 200, "body": "✅ Bot ran successfully from Vercel!"}
    except Exception as e:
        return {"statusCode": 500, "body": f"❌ Bot crashed: {str(e)}"}
