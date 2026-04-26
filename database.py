CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    senha TEXT,
    criado_em TEXT,
    trial_expira_em TEXT,
    ativo INTEGER DEFAULT 0
);
def criar_tabela_usuarios():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            senha TEXT,
            criado_em TEXT,
            trial_ate TEXT,
            pago_ate TEXT
        )
    """)

    conn.commit()
    conn.close()