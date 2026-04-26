from fastapi import FastAPI
from auth import login_user, register_user, ativar_usuario
from database import init_db
from pydantic import BaseModel
from pagamentos import criar_pix

app = FastAPI()


# =========================
# 📦 MODELS
# =========================
class UserAuth(BaseModel):
    email: str
    senha: str
    device_id: str | None = None  # 👈 NOVO


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
# 👤 REGISTER (COM DEVICE_ID)
# =========================
@app.post("/register")
def register(data: UserAuth):
    return register_user(
        data.email,
        data.senha,
        data.device_id  # 👈 AQUI
    )


# =========================
# 💳 PAGAMENTO (SIMULADO)
# =========================

@app.post("/pagar")
def pagar(data: EmailRequest):
    return criar_pix(data.email)


# =========================
# ✅ CONFIRMAR PAGAMENTO
# =========================
@app.post("/confirmar_pagamento")
def confirmar(data: EmailRequest):
    ativar_usuario(data.email)
    return {"status": "liberado"}