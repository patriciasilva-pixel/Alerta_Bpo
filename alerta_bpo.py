import requests
import os
from datetime import datetime, timedelta
import pytz
from flask import Flask

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
FUSO = pytz.timezone('America/Sao_Paulo')

@app.route('/')
def home():
    enviados = executar_bot()
    return f"Status: OK | Alertas na janela: {enviados} | Check: {datetime.now(FUSO).strftime('%H:%M:%S')}", 200

def executar_bot():
    try:
        res = requests.get(METABASE_URL, timeout=30)
        dados = res.json()
        
        contagem = 0
        agora = datetime.now(FUSO)
        
        # DEFINA AQUI O TEMPO (em minutos) PARA TRÁS QUE ELE DEVE OLHAR
        # Se agora são 10h30 e você quer pegar desde as 06h00, use 270 minutos.
        minutos_atras = 300 
        limite = agora - timedelta(minutes=minutos_atras)

        for linha in dados:
            data_str = linha.get('data_ajuste')
            if data_str:
                # Converte a data do Metabase para o horário de Brasília
                data_obj = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC).astimezone(FUSO)
                
                # Se o ajuste aconteceu dentro da nossa janela (ex: desde as 06h)
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
            f"🚨 *Ajuste Detectado (Operação Hoje)*\n"
            f"📦 *Pedido:* `{item.get('order_number')}`\n"
            f"🍎 *Produto:* {item.get('product')}\n"
            f"💰 *Preço:* R$ {item.get('preco_original')} -> R$ {item.get('valor_ajuste')}\n"
            f"👤 *BPO:* {item.get('email')}\n"
            f"⏰ *Hora:* {item.get('data_ajuste')}"
        )
    }
    requests.post(SLACK_WEBHOOK, json=msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
