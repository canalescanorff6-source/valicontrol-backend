from fastapi import FastAPI, Header, Request
from pydantic import BaseModel
from database import conectar
from auth import ativar_usuario
from datetime import datetime

app = FastAPI()

ADMIN_TOKEN = "ADMIN_MASTER_KEY"


# =========================
# 🔐 VALIDA TOKEN
# =========================
def get_email_by_token(token: str):
    if not token:
        return None

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE token=%s", (token,))
    user = cursor.fetchone()

    conn.close()

    return user[0] if user else None


# =========================
# 📦 MODELS
# =========================
class Produto(BaseModel):
    codigo: str
    nome: str
    validade: str
    quantidade: int


class EmailRequest(BaseModel):
    email: str


# =========================
# 📦 PRODUTOS
# =========================
@app.get("/produtos")
def listar_produtos(token: str = Header(None)):
    email = get_email_by_token(token)

    if not email:
        return {"erro": "Token inválido"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, validade, quantidade
        FROM produtos
        WHERE user_email=%s
        ORDER BY id DESC
    """, (email,))

    dados = cursor.fetchall()
    conn.close()

    return dados


@app.post("/produtos")
def adicionar_produto(data: Produto, token: str = Header(None)):
    email = get_email_by_token(token)

    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO produtos (codigo, nome, validade, quantidade, user_email)
        VALUES (%s, %s, %s, %s, %s)
    """, (data.codigo, data.nome, data.validade, data.quantidade, email))

    conn.commit()
    conn.close()

    return {"ok": True}


@app.delete("/produtos/{id}")
def excluir_produto(id: int, token: str = Header(None)):
    email = get_email_by_token(token)

    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM produtos
        WHERE id=%s AND user_email=%s
    """, (id, email))

    conn.commit()
    conn.close()

    return {"ok": True}


@app.put("/produtos/{id}")
def atualizar_produto(id: int, data: Produto, token: str = Header(None)):
    email = get_email_by_token(token)

    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE produtos
        SET codigo=%s, nome=%s, validade=%s, quantidade=%s
        WHERE id=%s AND user_email=%s
    """, (data.codigo, data.nome, data.validade, data.quantidade, id, email))

    conn.commit()
    conn.close()

    return {"ok": True}


# =========================
# 👑 ADMIN
# =========================
@app.get("/admin/users")
def admin_users(token: str = Header(None)):
    if token != ADMIN_TOKEN:
        return {"erro": "acesso negado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT email, criado_em, trial_expira_em, ativo
        FROM users
        ORDER BY criado_em DESC
    """)

    dados = cursor.fetchall()
    conn.close()

    res = []

    for u in dados:
        email, criado, trial, ativo = u

        agora = datetime.now()
        dias = (trial - agora).days if trial else 0

        if agora <= trial:
            status = "trial"
        elif ativo == 1:
            status = "ativo"
        else:
            status = "bloqueado"

        res.append({
            "email": email,
            "status": status,
            "dias_restantes": max(0, dias)
        })

    return res


@app.post("/admin/ativar")
def admin_ativar(data: EmailRequest, token: str = Header(None)):
    if token != ADMIN_TOKEN:
        return {"erro": "acesso negado"}

    ativar_usuario(data.email)
    return {"ok": True}


@app.post("/admin/bloquear")
def admin_bloquear(data: EmailRequest, token: str = Header(None)):
    if token != ADMIN_TOKEN:
        return {"erro": "acesso negado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET ativo=0, trial_expira_em=NOW()
        WHERE email=%s
    """, (data.email,))

    conn.commit()
    conn.close()

    return {"ok": True}


# =========================
# 🧪 TESTE
# =========================
@app.get("/")
def home():
    return {"status": "API ONLINE 🚀"}