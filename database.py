import psycopg2
import os

def conectar():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def init_db():
    conn = conectar()
    cursor = conn.cursor()

    # =========================
    # 👤 USERS
    # =========================
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

    # =========================
    # 📦 PRODUTOS (ESSENCIAL)
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            codigo TEXT,
            nome TEXT,
            validade TEXT,
            quantidade INTEGER,
            user_email TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("✅ PostgreSQL pronto")