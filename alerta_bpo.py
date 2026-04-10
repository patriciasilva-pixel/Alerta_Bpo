import requests
import os
import csv
from datetime import datetime

# --- CONFIGURAÇÕES ---
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    """Lê os IDs do ficheiro CSV para uma lista"""
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        # Lê cada linha e remove espaços/quebras de linha
        return [linha.strip() for linha in f.readlines()]

def registrar_envio(pedido_id):
    """Adiciona o novo ID ao ficheiro CSV com timestamp"""
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    # Formato: ID_DATA_HORA (conforme a imagem que mostraste)
    entrada = f"{pedido_id}_{agora}"
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"\n{entrada}")

def ja_enviado_hoje(pedido_id, lista_enviados):
    """Verifica se o ID do pedido já consta no histórico de hoje"""
    hoje = datetime.now().strftime('%d/%m/%Y')
    for item in lista_enviados:
        # Verifica se o ID e a data de hoje estão na mesma linha
        if pedido_id in item and hoje in item:
            return True
    return False

def main():
    enviados = carregar_enviados()
    
    try:
        response = requests.get(METABASE_PUBLIC_URL)
        response.raise_for_status()
        dados = response.json()
    except Exception as e:
        print(f"Erro ao aceder ao Metabase: {e}")
        return

    for row in dados:
        # Ajusta 'id_pedido' para o nome da coluna no teu Metabase
        pedido_id = str(row.get('id_pedido') or row.get('ID'))
        
        if not pedido_id or pedido_id == 'None':
            continue

        if not ja_enviado_hoje(pedido_id, enviados):
            msg_slack = {
                "text": (
                    f"🚨 *Alerta de Ajuste no Pedido*\n"
                    f"*Produto:* {row.get('product', 'N/A')}\n"
                    f"*Analista:* {row.get('analista', 'N/A')}\n"
                    f"*Email:* {row.get('email', 'N/A')}\n"
                    f"*Ajuste (%):* {row.get('perc_ajuste', 0)}%\n"
                    f"*Data:* {row.get('data_ajuste', 'N/A')}"
                )
            }
            
            res = requests.post(SLACK_WEBHOOK_URL, json=msg_slack)
            
            if res.status_code == 200:
                registrar_envio(pedido_id)
                print(f"✅ Enviado: {pedido_id}")
            else:
                print(f"❌ Erro Slack: {res.status_code}")
        else:
            print(f"⏭️ Pedido {pedido_id} já enviado hoje. Ignorando.")

if __name__ == "__main__":
    main()
