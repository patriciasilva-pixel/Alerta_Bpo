import requests
import os
from datetime import datetime, timedelta
from flask import Flask

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

@app.route('/')
def home():
    mensagens_enviadas = executar_bot()
    return f"Status: OK | Alertas enviados: {mensagens_enviadas} | Hora: {datetime.now().strftime('%H:%M:%S')}", 200

def executar_bot():
    try:
        res = requests.get(METABASE_URL, timeout=30)
        dados = res.json()
        
        contagem = 0
        agora = datetime.now()
        # Define a janela de tempo (ex: ajustes dos últimos 2 minutos)
        limite_tempo = agora - timedelta(minutes=2)

        for linha in dados:
            # Pega a data do ajuste (ajuste o nome da coluna 'Data' se for diferente no seu Metabase)
            # Supondo que a coluna de data se chama 'created_at' ou 'Data do Ajuste'
            data_ajuste_str = linha.get('Data do Ajuste') or linha.get('created_at')
            
            if data_ajuste_str:
                # Converte o texto da data para objeto real de tempo
                data_ajuste = datetime.strptime(data_ajuste_str[:19], "%Y-%m-%dT%H:%M:%S")
                
                # SÓ ENVIA SE FOR NOVO (Dentro da janela de 2 minutos)
                if data_ajuste > limite_tempo:
                    enviar_slack(linha)
                    contagem += 1
        
        return contagem
    except Exception as e:
        print(f"Erro: {e}")
        return 0

def enviar_slack(item):
    # Personalize aqui com as colunas do seu Metabase
    msg = {
        "text": f"🚨 *Novo Ajuste Detectado!*\n"
                f"*Pedido:* {item.get('Pedido', 'N/A')}\n"
                f"*Valor:* R$ {item.get('Valor', '0')}\n"
                f"*BPO:* {item.get('Nome BPO', 'N/A')}"
    }
    requests.post(SLACK_WEBHOOK, json=msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
