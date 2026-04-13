import requests
import os
import time
from datetime import datetime

# --- CONFIGURAÇÕES ---
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    if not os.path.exists(CSV_FILE): return set()
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        return set(linha.strip() for linha in f.readlines() if linha.strip())

def registrar_envio(id_unico):
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"{id_unico}\n")

def formatar_valor(valor, sufixo=""):
    try:
        if valor is None or str(valor).strip() in ["", "0", "0.0", "0.00"]: return "-"
        num = float(valor)
        if num == 0: return "-"
        if sufixo == "R$ ": return f"R$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{num}{sufixo}"
    except: return "-"

def main():
    print("🚀 Iniciando verificação...")
    # Pequena pausa para o GitHub organizar os arquivos antes de começar
    time.sleep(5) 
    
    enviados = carregar_enviados()
    
    try:
        res = requests.get(METABASE_PUBLIC_URL)
        dados = res.json()
    except: return

    for row in dados:
        pedido_id = str(row.get('order_number'))
        data_raw = str(row.get('data_ajuste', ''))
        
        # CHAVE ÚNICA (ID + DATA + HORA)
        id_unico = f"{pedido_id}_{data_raw.split('.')[0]}"

        if id_unico not in enviados:
            status_regra = str(row.get('status_alerta', 'OK')).upper()
            
            try:
                dt = datetime.strptime(data_raw.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                data_exibicao = dt.strftime('%d/%m/%Y %H:%M')
            except:
                data_exibicao = data_raw.replace('T', ' ').split('.')[0]

            header = "*ALERTA DE AJUSTE CRÍTICO*" if "CRIT" in status_regra else "*NOTIFICAÇÃO DE AJUSTE DE PEDIDO*"
            
            msg_slack = {
                "text": (
                    f"{header}\n"
                    f"──────────────────────────────\n"
                    f"*Status:* {'CRÍTICO' if 'CRIT' in status_regra else 'OK'}\n"
                    f"*ID do Pedido:* {pedido_id}\n"
                    f"*Produto:* {row.get('product', 'N/A')}\n"
                    f"*Analista:* {row.get('analista', 'N/A')}\n"
                    f"*Ajuste:* {formatar_valor(row.get('perc_ajuste'), '%')}\n"
                    f"*Valor:* {formatar_valor(row.get('valor_ajuste'), 'R$ ')}\n"
                    f"*Data:* {data_exibicao}\n"
                    f"──────────────────────────────"
                )
            }
            
            # Envia e já adiciona ao histórico LOCAL para não repetir no mesmo loop
            if requests.post(SLACK_WEBHOOK_URL, json=msg_slack).status_code == 200:
                registrar_envio(id_unico)
                enviados.add(id_unico)
                print(f"✅ Enviado: {pedido_id}")
                # Pausa entre mensagens para não sobrecarregar o Slack
                time.sleep(1) 

if __name__ == "__main__":
    main()
