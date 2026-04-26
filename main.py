from fastapi import FastAPI
from backend.auth import login_user, register_user, ativar_usuario
from core.database import init_db
from pydantic import BaseModel

app = FastAPI()


# =========================
# 📦 MODELS
# =========================
class UserAuth(BaseModel):
    email: str
    senha: str


class EmailRequest(BaseModel):
    email: str


# =========================
# 🚀 STARTUP
# =========================
@app.on_event("startup")
def startup():
    init_db()


# =========================
# 🔑 LOGIN
# =========================
@app.post("/login")
def login(data: UserAuth):
    return login_user(data.email, data.senha)


# =========================
# 👤 REGISTER
# =========================
@app.post("/register")
def register(data: UserAuth):
    return register_user(data.email, data.senha)


# =========================
# 💳 PAGAMENTO (simples)
# =========================
@app.post("/pagar")
def pagar(data: EmailRequest):
    return {"qr": "PIX-FAKE-123"}


# =========================
# ✅ CONFIRMAR PAGAMENTO
# =========================
@app.post("/confirmar_pagamento")
def confirmar(data: EmailRequest):
    ativar_usuario(data.email)
    return {"status": "liberado"}