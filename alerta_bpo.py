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
    return f"Status: OK | Enviados: {enviados} | Hora Br: {datetime.now(FUSO).strftime('%H:%M:%S')}", 200

def executar_bot():
    try:
        res = requests.get(METABASE_URL, timeout=30)
        dados = res.json()
        
        # 1. ORDENAR: Do mais novo para o mais antigo (Sua ideia)
        dados = sorted(dados, key=lambda x: x.get('data_ajuste', ''), reverse=True)
        
        contagem = 0
        agora_br = datetime.now(FUSO)
        
        # 2. JANELA DE SEGURANÇA: Aumentei para 10 minutos para o teste inicial
        limite_br = agora_br - timedelta(minutes=10)
        
        ids_processados = set()

        for linha in dados:
            data_str = linha.get('data_ajuste')
            pedido_id = linha.get('order_number')

            if data_str:
                # 3. TRATAMENTO DE DATA: Forçamos a leitura ignorando o fuso do servidor
                # Lemos os primeiros 19 caracteres (YYYY-MM-DDTHH:MM:SS)
                data_crua = datetime.strptime(data_str[:19], "%Y-%m-%dT%H:%M:%S")
                
                # IMPORTANTE: Se o Metabase já envia a hora de Brasília no texto, 
                # dizemos ao Python que essa hora JÁ É de Brasília.
                data_obj_br = FUSO.localize(data_crua)
                
                # 4. FILTRO DE JANELA
                if data_obj_br > limite_br:
                    if pedido_id not in ids_processados:
                        enviar_slack(linha)
                        ids_processados.add(pedido_id)
                        contagem += 1
                else:
                    # Como está ordenado, se o primeiro não entrar, os outros também não entrarão
                    break 
                    
        return contagem
    except Exception as e:
        print(f"Erro no bot: {e}")
        return 0

def enviar_slack(item):
    status = str(item.get('status_alerta', 'OK')).upper()
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
