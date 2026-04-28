from fastapi import FastAPI, Header
from pydantic import BaseModel

from database import init_db, conectar
from auth import login_user, register_user
from pagamentos import criar_pagamento

app = FastAPI()


@app.on_event("startup")
def start():
    init_db()
    print("🚀 API ONLINE")


class UserAuth(BaseModel):
    email: str
    senha: str
    device_id: str


class Produto(BaseModel):
    codigo: str
    nome: str
    validade: str
    quantidade: int


class PayRequest(BaseModel):
    email: str


def get_email(token):
    if not token:
        return None

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE token=%s", (token,))
    user = cursor.fetchone()

    conn.close()
    return user[0] if user else None


# 🔐 LOGIN
@app.post("/login")
def login(data: UserAuth):
    return login_user(data.email, data.senha, data.device_id)


# 👤 REGISTER
@app.post("/register")
def register(data: UserAuth):
    return register_user(data.email, data.senha, data.device_id)


# 💳 PAGAMENTO
@app.post("/pagar")
def pagar(data: PayRequest):
    return criar_pagamento(data.email)


# 📦 PRODUTOS
@app.get("/produtos")
def listar(token: str = Header(None)):
    email = get_email(token)
    if not email:
        return {"erro": "não autorizado"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, validade, quantidade
        FROM produtos WHERE user_email=%s
    """, (email,))

    dados = cursor.fetchall()
    conn.close()

    return dados


@app.post("/produtos")
def add(data: Produto, token: str = Header(None)):
    email = get_email(token)
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
    email = get_email_by_token(token)

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


@app.get("/")
def home():
    return {"status": "API ONLINE"}
