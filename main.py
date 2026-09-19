from pathlib import Path
from app.dotenv import load_dotenv

if __name__ == "__main__":
    env_path = Path(__file__).resolve().parent / ".env"
    if not load_dotenv(str(env_path)):
        raise SystemExit(f".env not found at {env_path}")

    from app.logging_setup import setup_logger
    from app.repositories.mongodb import init_mongo
    from app.server import run

    setup_logger()
    init_mongo()
    run()