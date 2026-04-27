# backend/database.py

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
            ativo INTEGER DEFAULT 0,
            device_id TEXT
        )
    """)

    # =========================
    # 📦 PRODUTOS
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

    # =========================
    # 🔥 GARANTIR COLUNA (ESSENCIAL)
    # =========================
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='produtos'
                AND column_name='user_email'
            ) THEN
                ALTER TABLE produtos ADD COLUMN user_email TEXT;
            END IF;
        END
        $$;
    """)

    conn.commit()
    conn.close()

    print("✅ DB OK + coluna garantida")