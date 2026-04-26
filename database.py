import psycopg2
import os

def conectar():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def init_db():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE,
            senha TEXT,
            token TEXT,
            criado_em TIMESTAMP,
            trial_expira_em TIMESTAMP,
            ativo INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

    print("✅ PostgreSQL pronto")