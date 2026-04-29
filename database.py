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
                plano TEXT DEFAULT 'trial',
                is_admin BOOLEAN DEFAULT FALSE
            )
        """)

        # 🔥 MIGRAÇÃO SEGURA is_admin
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name='users'
                    AND column_name='is_admin'
                ) THEN
                    ALTER TABLE users
                    ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
                END IF;
            END$$;
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

        # 🔥 MIGRAÇÃO tipo_qtd
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
        # 💳 PAGAMENTOS
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
        print("✅ BANCO OK (COM MIGRAÇÃO)")

    except Exception as e:
        print("❌ ERRO INIT DB:", e)
        conn.rollback()

    finally:
        conn.close()
