from fastapi import FastAPI
from auth import (
    login_user,
    register_user,
    ativar_usuario,
    criar_tabela
)
from pagamentos import criar_pix

app = FastAPI()


# =========================
# 🚀 INICIALIZAÇÃO SEGURA
# =========================
@app.on_event("startup")
def startup():
    try:
        criar_tabela()
        print("✅ Banco inicializado")
    except Exception as e:
        print("❌ Erro ao criar tabela:", e)


# =========================
# 💳 PAGAMENTO (PIX)
# =========================
@app.post("/pagar")
def pagar(data: dict):
    try:
        return criar_pix(data["email"])
    except Exception as e:
        return {"erro": str(e)}


# =========================
# 🔑 LOGIN
# =========================
@app.post("/login")
def login(data: dict):
    try:
        return login_user(data["email"], data["senha"])
    except Exception as e:
        return {"erro": str(e)}


# =========================
# 👤 REGISTRO
# =========================
@app.post("/register")
def register(data: dict):
    try:
        return register_user(data["email"], data["senha"])
    except Exception as e:
        return {"erro": str(e)}


# =========================
# 🧪 CONFIRMAÇÃO
# =========================
@app.post("/confirmar_pagamento")
def confirmar_pagamento(data: dict):
    try:
        ativar_usuario(data["email"])
        return {"status": "liberado"}
    except Exception as e:
        return {"erro": str(e)}