import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from database import conectar


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def gerar_token():
    return str(uuid.uuid4())


# =========================
# 🧾 REGISTER
# =========================
def register_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return {"erro": "Email já existe"}

        agora = datetime.now(timezone.utc)
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
        return {"status": "ok"}

    except Exception as e:
        print("ERRO REGISTER:", e)
        return {"erro": "falha ao criar conta"}

    finally:
        conn.close()


# =========================
# 🔐 LOGIN
# =========================
def login_user(email, senha, device_id):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT senha, trial_expira_em, ativo, device_id
            FROM users WHERE email=%s
        """, (email,))

        user = cursor.fetchone()

        if not user:
            return {"erro": "Usuário não existe"}

        senha_db, trial_expira, ativo, device_db = user

        # 🔑 senha
        if hash_senha(senha) != senha_db:
            return {"erro": "Senha inválida"}

        # 🔒 bloqueio por máquina
        if device_db and device_db != device_id:
            return {"erro": "Conta já usada em outro dispositivo"}

        # 💻 salva device se vazio
        if not device_db:
            cursor.execute(
                "UPDATE users SET device_id=%s WHERE email=%s",
                (device_id, email)
            )

        agora = datetime.now(timezone.utc)

        # ⛔ expirado
        if trial_expira and agora > trial_expira and ativo == 0:
            return {
                "status": "bloqueado",
                "msg": "Trial expirado"
            }

        # ⏳ dias restantes
        dias_restantes = 0
        if trial_expira:
            dias_restantes = max(0, (trial_expira - agora).days)

        token = gerar_token()

        cursor.execute(
            "UPDATE users SET token=%s WHERE email=%s",
            (token, email)
        )

        conn.commit()

        return {
            "status": "ok",
            "token": token,
            "dias_restantes": dias_restantes
        }

    except Exception as e:
        print("ERRO LOGIN:", e)
        return {"erro": "falha no login"}

    finally:
        conn.close()
