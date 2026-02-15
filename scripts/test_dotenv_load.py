import os, traceback

try:
    from app import create_app

    app = create_app()
    print("✅ create_app() ejecutado")
    print("FLASK_ENV env var:", os.environ.get("FLASK_ENV"))
    print("App config ENV:", app.config.get("ENV"))
    print("App DEBUG:", app.config.get("DEBUG"))
    sk = app.config.get("SECRET_KEY")
    print("SECRET_KEY:", "SET" if sk else "MISSING")
    print(
        "DATABASE_URI preview:",
        (app.config.get("SQLALCHEMY_DATABASE_URI") or "N/A")[:200],
    )
except Exception as e:
    print("❌ Exception:")
    traceback.print_exc()
    print("--- end traceback ---")
