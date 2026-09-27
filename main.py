if __name__ == "__main__":
    from app.logging_setup import setup_logger
    from app.database import init_db, ensure_all
    from app.server import run

    setup_logger()
    init_db()
    ensure_all()
    run()