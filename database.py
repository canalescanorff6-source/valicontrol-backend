import psycopg2
import os


# =========================
# 🔌 CONEXÃO
# =========================
def conectar():
    url = os.getenv("DATABASE_URL")

    if not url:
        raise Exception("DATABASE_URL não definida")

    # 🔥 Render usa SSL obrigatoriamente
    return psycopg2.connect(url, sslmode="require")


# =========================
# 🚀 INIT DB (ROBUSTO)
# =========================
def init_db():
    conn = conectar()
    cursor = conn.cursor()

    try:
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
        # 📦 PRODUTOS
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

        # 🔥 MIGRAÇÃO SEGURA tipo_qtd
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name='produtos'
                    AND column_name='tipo_qtd'
                ) THEN
                    ALTER TABLE produtos
                    ADD COLUMN tipo_qtd TEXT DEFAULT 'Un';
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

        # =========================
        # 💳 PAGAMENTOS (🔥 NOVO)
        # =========================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamentos (
                id SERIAL PRIMARY KEY,
                payment_id TEXT UNIQUE,
                email TEXT,
                status TEXT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        print("✅ BANCO OK")

    except Exception as e:
        print("❌ ERRO INIT DB:", e)
        conn.rollback()

    finally:
        conn.close()
