"""PostgreSQL connection helper."""

import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "finguard"),
        password=os.getenv("POSTGRES_PASSWORD", "finguard"),
        dbname=os.getenv("POSTGRES_DB", "finguard"),
        cursor_factory=RealDictCursor,
    )
