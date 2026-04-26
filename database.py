import sqlite3

DB = "banco.db"

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
                                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                                             email TEXT UNIQUE,
                                             senha TEXT,
                                             token TEXT,
                                             criado_em TEXT,
                                             trial_expira_em TEXT,
                                             ativo INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Banco pronto")