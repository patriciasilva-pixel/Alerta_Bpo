import requests
import os
import csv
from datetime import datetime

# --- CONFIGURAÇÕES ---
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        return [linha.strip() for linha in f.readlines()]

def registrar_envio(pedido_id):
    hoje = datetime.now().strftime('%d/%m/%Y')
    entrada = f"{pedido_id}_{hoje}"
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"\n{entrada}")

def main():
    print("Iniciando verificação de ajustes (Modo Profissional)...")
    enviados = carregar_enviados()
    
    try:
        response = requests.get(METABASE_PUBLIC_URL)
        response.raise_for_status()
        dados = response.json()
    except Exception as e:
        print(f"Erro ao acessar Metabase: {e}")
        return

    for row in dados:
        pedido_id = str(row.get('order_number'))
        status_regra = str(row.get('status_alerta', 'OK')).upper()
        hoje = datetime.now().strftime('%d/%m/%Y')
        
        if not pedido_id or pedido_id == 'None':
            continue

        identificador = f"{pedido_id}_{hoje}"
        
        if identificador not in enviados:
            # --- FORMATAÇÃO DE DATA ---
            data_raw = row.get('data_ajuste', 'N/A')
            try:
                dt_obj = datetime.strptime(data_raw.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                data_exibicao = dt_obj.strftime('%d/%m/%Y %H:%M')
            except:
                data_exibicao = data_raw.replace('T', ' ').split('.')[0]

            # --- MENSAGEM PROFISSIONAL (SEM EMOJIS EXCESSIVOS) ---
            # Mantivemos apenas o indicador de status solicitado
            if 'CRÍTICO' in status_regra or 'CRITICO' in status_regra:
                header = "*ALERTA DE AJUSTE CRÍTICO*"
                status_line = "*Status:* CRÍTICO"
            else:
                header = "*NOTIFICAÇÃO DE AJUSTE DE PEDIDO*"
                status_line = "*Status:* OK"

            msg_slack = {
                "text": (
                    f"{header}\n"
                    f"──────────────────────────────\n"
                    f"{status_line}\n"
                    f"*ID do Pedido:* {pedido_id}\n"
                    f"*Produto:* {row.get('product', 'N/A')}\n"
                    f"*Analista Responsável:* {row.get('analista', 'N/A')}\n"
                    f"*Percentual de Ajuste:* {row.get('perc_ajuste', 0)}%\n"
                    f"*Valor do Ajuste:* R$ {row.get('valor_ajuste', 0)}\n"
                    f"*Data do Evento:* {data_exibicao}\n"
                    f"──────────────────────────────"
                )
            }
            
            res = requests.post(SLACK_WEBHOOK_URL, json=msg_slack)
            
            if res.status_code == 200:
                registrar_envio(pedido_id)
                print(f"✅ Notificação enviada: {pedido_id}")
            else:
                print(f"❌ Erro de conexão com Slack: {res.status_code}")

if __name__ == "__main__":
    main()
