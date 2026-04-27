from fastapi import Request
from auth import ativar_usuario  # 🔥 IMPORTANTE
import mercadopago
import os

sdk = mercadopago.SDK("APP_USR-7644007864092484-042523-6627b8e270268c808eee183961e284e4-3361329264")

def criar_pix(email):
    try:
        payment_data = {
            "transaction_amount": 29.90,
            "description": "Plano ValiControl",
            "payment_method_id": "pix",
            "payer": {
                "email": email
            }
        }

        payment = sdk.payment().create(payment_data)

        print("📥 RESPOSTA COMPLETA MP:", payment)

        response = payment.get("response", {})

        if not response:
            return {"erro": "Resposta vazia do Mercado Pago"}

        # 🔥 VALIDA SE VEIO PIX
        poi = response.get("point_of_interaction")

        if not poi:
            return {
                "erro": "Pagamento não gerou PIX",
                "debug": response
            }

        transaction = poi.get("transaction_data", {})

        return {
            "qr": transaction.get("qr_code"),
            "qr_base64": transaction.get("qr_code_base64"),
            "payment_id": response.get("id"),
            "status": response.get("status")
        }

    except Exception as e:
        print("💥 ERRO PIX:", e)
        return {"erro": str(e)}