from core.database import conectar
import hashlib
import uuid
from datetime import datetime, timedelta


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_device():
    return str(uuid.uuid4())


def gerar_token(email):
    token = str(uuid.uuid4())

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET token=? WHERE email=?",
        (token, email)
    )

    conn.commit()
    conn.close()

    return token


def register_user(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        conn.close()
        return {"erro": "Usuário já existe"}

    agora = datetime.now()
    trial = agora + timedelta(days=7)

    try:
        cursor.execute("""
            INSERT INTO users (
                email, senha, criado_em, trial_expira_em, ativo, device_id
            )
            VALUES (?, ?, ?, ?, 0, ?)
        """, (
            email,
            hash_senha(senha),
            agora.isoformat(),
            trial.isoformat(),
            gerar_device()
        ))

        conn.commit()
        return {"status": "ok"}

    except Exception as e:
        return {"erro": str(e)}

    finally:
        conn.close()


def login_user(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT senha, trial_expira_em, ativo
        FROM users
        WHERE email=?
    """, (email,))

    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"erro": "Usuário não existe"}

    senha_db, trial_expira, ativo = user

    if hash_senha(senha) != senha_db:
        conn.close()
        return {"erro": "Senha inválida"}

    agora = datetime.now()
    trial_expira = datetime.fromisoformat(trial_expira)

    if agora <= trial_expira:
        status = "trial"
    elif ativo == 1:
        status = "ativo"
    else:
        conn.close()
        return {"status": "bloqueado"}

    token = gerar_token(email)

    conn.close()

    return {
        "status": status,
        "token": token
    }


def ativar_usuario(email):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET ativo=1 WHERE email=?",
        (email,)
    )

    conn.commit()
    conn.close()