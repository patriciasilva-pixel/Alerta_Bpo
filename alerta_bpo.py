import requests
import os
from datetime import datetime, timedelta
import pytz
from flask import Flask

app = Flask(__name__)

METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
FUSO = pytz.timezone('America/Sao_Paulo')

@app.route('/')
def home():
    enviados = executar_bot()
    return f"Status: OK | Alertas: {enviados} | Hora Br: {datetime.now(FUSO).strftime('%H:%M:%S')}", 200

def executar_bot():
    try:
        # Pega a hora exata de Brasília agora
        agora_br = datetime.now(FUSO)
        
        # Trava de horário de operação
        if agora_br.hour < 6 or agora_br.hour >= 22:
            return 0

        res = requests.get(METABASE_URL, timeout=30)
        dados = res.json()
        
        contagem = 0
        # Aumentei para 5 minutos de janela para dar mais folga
        limite_br = agora_br - timedelta(minutes=5)

        for linha in dados:
            data_str = linha.get('data_ajuste')
            if data_str:
                # Converte a data do Metabase (que vem em UTC) diretamente para Brasília
                data_obj_br = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc).astimezone(FUSO)
                
                # Compara hora de Brasília com hora de Brasília
                if data_obj_br > limite_br:
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
