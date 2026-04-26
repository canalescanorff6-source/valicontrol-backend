from fastapi import FastAPI
from auth import (
    login_user,
    register_user,
    ativar_usuario,
    criar_tabela
)
from pagamentos import criar_pix

# 🔥 cria tabela automaticamente ao subir backend
criar_tabela()

app = FastAPI()


# =========================
# 💳 PAGAMENTO (PIX)
# =========================
@app.post("/pagar")
def pagar(data: dict):
    return criar_pix(data["email"])


# =========================
# 🔑 LOGIN
# =========================
@app.post("/login")
def login(data: dict):
    return login_user(data["email"], data["senha"])


# =========================
# 👤 REGISTRO
# =========================
@app.post("/register")
def register(data: dict):
    return register_user(data["email"], data["senha"])


# =========================
# 🧪 CONFIRMAÇÃO (TESTE)
# =========================
@app.post("/confirmar_pagamento")
def confirmar_pagamento(data: dict):
    email = data["email"]

    ativar_usuario(email)

    return {"status": "liberado"}

#@app.post("/webhook")
#def webhook(data: dict):
    #    if data["type"] == "payment":
        # validar pagamento aqui
    #        email = pegar_email_do_pagamento(data)

    #        ativar_usuario(email)

#    return {"ok": True}