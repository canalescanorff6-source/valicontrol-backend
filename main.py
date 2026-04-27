from fastapi import FastAPI, Header
from database import conectar
from auth_middleware import get_user_by_token
from auth import ativar_usuario
from pydantic import BaseModel

app = FastAPI()

ADMIN_TOKEN = "ADMIN_MASTER_KEY"


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
def listar(token: str = Header(None)):
    email = get_user_by_token(token)
    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, validade, quantidade
        FROM produtos
        WHERE user_email=%s
    """, (email,))

    dados = cursor.fetchall()
    conn.close()

    return dados


@app.post("/produtos")
def adicionar(data: Produto, token: str = Header(None)):
    email = get_user_by_token(token)
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
def excluir(id: int, token: str = Header(None)):
    email = get_user_by_token(token)
    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM produtos WHERE id=%s AND user_email=%s
    """, (id, email))

    conn.commit()
    conn.close()

    return {"ok": True}


@app.put("/produtos/{id}")
def atualizar(id: int, data: Produto, token: str = Header(None)):
    email = get_user_by_token(token)
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

    from datetime import datetime

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
            "dias": max(0, dias)
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
        UPDATE users SET ativo=0, trial_expira_em=NOW()
        WHERE email=%s
    """, (data.email,))

    conn.commit()
    conn.close()

    return {"ok": True}