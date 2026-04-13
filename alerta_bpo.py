import requests
import os
from datetime import datetime
from flask import Flask

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
METABASE_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

@app.route('/')
def home():
    # Toda vez que alguém (ou o cron-job) acessar o link, o robô roda
    resultado = executar_bot()
    return f"Status: {resultado} | Hora: {datetime.now().strftime('%H:%M:%S')}", 200

def executar_bot():
    print("🚀 Verificando Metabase...")
    try:
        res = requests.get(METABASE_URL, timeout=30)
        if res.status_code == 200:
            # Aqui ele processaria os dados (estamos simplificando para testar a conexão)
            return "Sucesso ao ler Metabase"
        else:
            return f"Erro Metabase: {res.status_code}"
    except Exception as e:
        return f"Erro: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
