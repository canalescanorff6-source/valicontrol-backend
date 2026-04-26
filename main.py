from fastapi import FastAPI
from backend.auth import login_user, register_user, ativar_usuario
from backend.pagamentos import criar_pix
from core.database import init_db

app = FastAPI()


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
def login(data: dict):
    return login_user(data["email"], data["senha"])


# =========================
# 👤 REGISTER
# =========================
@app.post("/register")
def register(data: dict):
    return register_user(data["email"], data["senha"])


# =========================
# 💳 PAGAR
# =========================
@app.post("/pagar")
def pagar(data: dict):
    return criar_pix(data["email"])


# =========================
# ✅ CONFIRMAR PAGAMENTO
# =========================
@app.post("/confirmar_pagamento")
def confirmar(data: dict):
    ativar_usuario(data["email"])
    return {"status": "liberado"}