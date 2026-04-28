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
            device_id TEXT,
            plano TEXT DEFAULT 'trial'
        )
    """)

    # =========================
    # 📦 PRODUTOS (CORRIGIDO)
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            codigo TEXT,
            nome TEXT,
            validade TEXT,
            quantidade INTEGER,
            tipo_qtd TEXT DEFAULT 'Un',
            user_email TEXT
        )
    """)

    # 🔥 GARANTE COLUNA CASO JÁ EXISTA TABELA ANTIGA
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name='produtos' AND column_name='tipo_qtd'
            ) THEN
                ALTER TABLE produtos ADD COLUMN tipo_qtd TEXT DEFAULT 'Un';
            END IF;
        END$$;
    """)

    # =========================
    # 🧾 LOGS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            email TEXT,
            acao TEXT,
            criado_em TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    conn.close()
