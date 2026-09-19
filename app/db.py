from app.repositories.mongodb import get_db


def ensure_collections():
    db = get_db()

    