import hashlib
import uuid
from datetime import datetime, timedelta
from database import conectar


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_token():
    return str(uuid.uuid4())


# =========================
# REGISTER
# =========================
def register_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        conn.close()
        return {"erro": "Email já existe"}

    agora = datetime.now()
    trial = agora + timedelta(days=15)

    cursor.execute("""
        INSERT INTO users (email, senha, criado_em, trial_expira_em, ativo, device_id)
        VALUES (%s, %s, %s, %s, 0, %s)
    """, (
        email,
        hash_senha(senha),
        agora,
        trial,
        device_id
    ))

    conn.commit()
    conn.close()

    return {"status": "ok"}


# =========================
# LOGIN (100% ESTÁVEL)
# =========================
def login_user(email, senha, device_id):
    conn = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT senha, trial_expira_em, ativo, device_id
            FROM users WHERE email=%s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return {"erro": "Usuário não existe"}

        senha_db, trial_expira, ativo, device_db = user

        # senha
        if hash_senha(senha) != senha_db:
            return {"erro": "Senha inválida"}

        # device lock
        if device_db and device_db != device_id:
            return {"erro": "Conta usada em outro dispositivo"}

        # salvar device na primeira vez
        if not device_db:
            cursor.execute(
                "UPDATE users SET device_id=%s WHERE email=%s",
                (device_id, email)
            )

        agora = datetime.now()

        # evita erro None
        if not trial_expira:
            trial_expira = agora

        # bloqueio
        if agora > trial_expira and ativo == 0:
            return {"status": "bloqueado"}

        token = gerar_token()

        cursor.execute(
            "UPDATE users SET token=%s WHERE email=%s",
            (token, email)
        )

        conn.commit()

        return {
            "status": "ok",
            "token": token,
            "trial_restante": max(0, (trial_expira - agora).days)
        }

    except Exception as e:
        print("ERRO LOGIN REAL:", e)
        return {"erro": str(e)}

    finally:
        if conn:
            conn.close()
