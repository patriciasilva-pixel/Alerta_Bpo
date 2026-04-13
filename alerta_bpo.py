import requests
import os
from datetime import datetime, timedelta
import pytz # Biblioteca para lidar com o horário do Brasil
from flask import Flask

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
FUSO = pytz.timezone('America/Sao_Paulo')

@app.route('/')
def home():
    enviados = executar_bot()
    return f"Status: OK | Novos alertas: {enviados} | Check: {datetime.now(FUSO).strftime('%H:%M:%S')}", 200

def executar_bot():
    try:
        res = requests.get(METABASE_URL, timeout=30)
        dados = res.json()
        
        contagem = 0
        agora = datetime.now(FUSO)
        # Janela de 2 minutos para garantir que pegamos o ajuste assim que ele sair no Meta
        limite = agora - timedelta(minutes=2)

        for linha in dados:
            data_str = linha.get('data_ajuste')
            if data_str:
                # O Metabase geralmente manda: "2026-04-13T18:46:00"
                data_obj = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC).astimezone(FUSO)
                
                if data_obj > limite:
                    enviar_slack(linha)
                    contagem += 1
        return contagem
    except Exception as e:
        print(f"Erro: {e}")
        return 0

def enviar_slack(item):
    msg = {
        "text": (
            f"🚨 *Novo Ajuste de Preço!*\n"
            f"📦 *Pedido:* `{item.get('order_number')}`\n"
            f"🍎 *Produto:* {item.get('product')}\n"
            f"💰 *Preço Orig:* R$ {item.get('preco_original')}\n"
            f"📉 *Valor Ajuste:* R$ {item.get('valor_ajuste')}\n"
            f"👤 *BPO:* {item.get('email')}\n"
            f"⏰ *Data:* {item.get('data_ajuste')}"
        )
    }
    requests.post(SLACK_WEBHOOK, json=msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
