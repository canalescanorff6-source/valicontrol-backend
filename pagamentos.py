import requests
import os
from dotenv import load_dotenv

load_dotenv()

ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
BASE_URL = "https://api.asaas.com/v3"

if not ASAAS_API_KEY:
    raise ValueError("API KEY não configurada")


# =========================
# 👤 CRIAR CLIENTE
# =========================
def criar_cliente(email):
    try:
        r = requests.post(
            f"{BASE_URL}/customers",
            headers={
                "access_token": ASAAS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "name": email,
                "email": email
            }
        )

        data = r.json()

        if "errors" in data:
            r2 = requests.get(
                f"{BASE_URL}/customers",
                headers={"access_token": ASAAS_API_KEY},
                params={"email": email}
            )

            clientes = r2.json().get("data", [])
            if clientes:
                return clientes[0]["id"]

            return None

        return data.get("id")

    except Exception as e:
        print("ERRO CLIENTE:", e)
        return None


# =========================
# 💳 CRIAR PIX
# =========================
def criar_pagamento(email):
    try:
        customer_id = criar_cliente(email)

        if not customer_id:
            return {"erro": "cliente inválido"}

        r = requests.post(
            f"{BASE_URL}/payments",
            headers={
                "access_token": ASAAS_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "customer": customer_id,
                "billingType": "PIX",
                "value": 10.0,
                "description": "Plano ValiControl",
                "externalReference": email  # 🔥 ligação com usuário
            }
        )

        data = r.json()

        if "errors" in data:
            print("ERRO ASAAS:", data)
            return {"erro": "erro ao criar pagamento"}

        payment_id = data["id"]

        r2 = requests.get(
            f"{BASE_URL}/payments/{payment_id}/pixQrCode",
            headers={"access_token": ASAAS_API_KEY}
        )

        qr_data = r2.json()

        if "errors" in qr_data:
            print("ERRO QR:", qr_data)
            return {"erro": "erro ao gerar QR"}

        return {
            "qr": qr_data.get("payload"),
            "qr_base64": qr_data.get("encodedImage"),
            "payment_id": payment_id,
            "customer_id": customer_id
        }

    except Exception as e:
        print("ERRO PIX:", e)
        return {"erro": "falha pagamento"}
