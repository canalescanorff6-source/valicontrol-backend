from fastapi import FastAPI, Header, Request
from pydantic import BaseModel
from database import conectar, init_db
from auth import login_user, register_user, ativar_usuario
from pagamentos import criar_pagamento
import os

app = FastAPI()

# MODELS
class UserAuth(BaseModel):
    email: str
    senha: str
    device_id: str

class Produto(BaseModel):
    codigo: str
    nome: str
    validade: str
    quantidade: int

# START
@app.on_event("startup")
def startup():
    init_db()
    print("🚀 API ONLINE")

# TOKEN
def get_email(token):
    if not token:
        return None

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE token=%s", (token,))
    user = cursor.fetchone()

    conn.close()
    return user[0] if user else None

# LOGIN
@app.post("/login")
def login(data: UserAuth):
    return login_user(data.email, data.senha, data.device_id)

# REGISTER
@app.post("/register")
def register(data: UserAuth):
    return register_user(data.email, data.senha, data.device_id)

# PAGAMENTO
@app.post("/pagamento")
def pagamento(data: UserAuth):
    return criar_pagamento(data.email)

# WEBHOOK
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("WEBHOOK:", data)

    try:
        if data.get("type") == "payment":
            from pagamentos import sdk

            payment_id = data["data"]["id"]
            payment = sdk.payment().get(payment_id)

            res = payment.get("response", {})
            status = res.get("status")
            email = res.get("external_reference")

            if status == "approved" and email:
                ativar_usuario(email)

    except Exception as e:
        print("ERRO WEBHOOK:", e)

    return {"ok": True}

# PRODUTOS
@app.get("/produtos")
def listar(token: str = Header(None)):
    email = get_email(token)
    if not email:
        return {"erro": "token inválido"}

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, codigo, nome, validade, quantidade
        FROM produtos WHERE user_email=%s
    """, (email,))

    dados = cursor.fetchall()
    conn.close()

    return dados


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
