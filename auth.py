from database import conectar
import hashlib
import uuid
from datetime import datetime, timedelta


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_token():
    return str(uuid.uuid4())


# =========================
# 🧾 REGISTER
# =========================
def register_user(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        conn.close()
        return {"erro": "Usuário já existe"}

    agora = datetime.now()
    trial = agora + timedelta(days=15)

    try:
        cursor.execute("""
            INSERT INTO users (email, senha, criado_em, trial_expira_em, ativo)
            VALUES (%s, %s, %s, %s, 0)
        """, (
            email,
            hash_senha(senha),
            agora,
            trial
        ))

        conn.commit()
        return {"status": "ok"}

    except Exception as e:
        return {"erro": str(e)}

    finally:
        conn.close()


# =========================
# 🔐 LOGIN
# =========================
def login_user(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    print("LOGIN:", email)

    cursor.execute("""
        SELECT senha, trial_expira_em, ativo
        FROM users
        WHERE email=%s
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

    # 🔥 segurança contra None
    if not trial_expira:
        trial_expira = agora

    # 📅 cálculo dias restantes
    dias_restantes = max(0, (trial_expira - agora).days)

    # status
    if agora <= trial_expira:
        status = "trial"
    elif ativo == 1:
        status = "ativo"
    else:
        conn.close()
        return {"status": "bloqueado"}

    token = gerar_token()

    cursor.execute(
        "UPDATE users SET token=%s WHERE email=%s",
        (token, email)
    )

    conn.commit()
    conn.close()

    return {
        "status": status,
        "token": token,
        "dias_restantes": dias_restantes if status == "trial" else None
    }


# =========================
# 💳 ATIVAR USUÁRIO
# =========================
def ativar_usuario(email):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET ativo=1 WHERE email=%s",
        (email,)
    )

    conn.commit()
    conn.close()