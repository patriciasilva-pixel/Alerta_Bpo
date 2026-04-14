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
    return f"Status: OK | Alertas Novos: {enviados} | Check: {datetime.now(FUSO).strftime('%H:%M:%S')}", 200

def executar_bot():
    try:
        agora = datetime.now(FUSO)
        
        # Trava de segurança: Só roda no horário de operação (06h às 22h)
        # Isso evita que o robô gaste todas as horas gratuitas do Render
        if agora.hour < 6 or agora.hour >= 22:
            return 0

        res = requests.get(METABASE_URL, timeout=30)
        dados = res.json()
        
        contagem = 0
        # Janela de 3 minutos para quem roda a cada 2 minutos
        limite = agora - timedelta(minutes=3)

        for linha in dados:
            data_str = linha.get('data_ajuste')
            if data_str:
                data_obj = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC).astimezone(FUSO)
                
                # Se o ajuste aconteceu agora (nos últimos 3 min)
                if data_obj > limite:
                    enviar_slack(linha)
                    contagem += 1
        return contagem
    except Exception as e:
        print(f"Erro: {e}")
        return 0

def enviar_slack(item):
    status = item.get('status_alerta', 'OK').upper()
    
    header = "*ATENÇÃO: MONITORAMENTO DE AJUSTE CRÍTICO*" if status == 'CRÍTICO' else "*RELATÓRIO DE AJUSTE DE PEDIDO*"

    msg = {
        "text": (
            f"{header}\n"
            f"--------------------------------------------------\n"
            f"*Status do Alerta:* {status}\n"
            f"*ID do Pedido:* `{item.get('order_number')}`\n"
            f"*Produto:* {item.get('product')}\n"
            f"*Preço Original:* R$ {item.get('preco_original')}\n"
            f"*Valor Ajustado:* R$ {item.get('valor_ajuste')}\n"
            f"*Responsável:* {item.get('analista')}\n"
            f"*Data/Hora Registro:* {item.get('data_ajuste')}\n"
            f"--------------------------------------------------"
        )
    }
    requests.post(SLACK_WEBHOOK, json=msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
