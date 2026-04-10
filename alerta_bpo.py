import requests
import os
from datetime import datetime

# --- CONFIGURAÇÕES ---
METABASE_PUBLIC_URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.json" 
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
CSV_FILE = 'enviados.csv'

def carregar_enviados():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        # Usamos um 'set' para busca rápida e evitar duplicados no carregamento
        return set(linha.strip() for linha in f.readlines() if linha.strip())

def registrar_envio(identificador):
    with open(CSV_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"{identificador}\n")

def formatar_valor(valor, sufixo=""):
    try:
        if valor is None or str(valor).strip() in ["", "0", "0.0", "0.00"]:
            return "-"
        num = float(valor)
        if num == 0: return "-"
        if sufixo == "R$ ":
            return f"{sufixo}{num:.2f}".replace('.', ',')
        return f"{num}{sufixo}"
    except:
        return "-"

def main():
    print("Iniciando verificação...")
    enviados = carregar_enviados()
    
    try:
        res = requests.get(METABASE_PUBLIC_URL)
        dados = res.json()
    except Exception as e:
        print(f"Erro Metabase: {e}")
        return

    for row in dados:
        pedido_id = str(row.get('order_number'))
        data_ajuste_raw = str(row.get('data_ajuste', ''))
        
        if not pedido_id or pedido_id == 'None':
            continue

        # CRIAMOS UM ID ÚNICO: Pedido + Data + Hora para ser exato
        # Isso evita repetir o mesmo ajuste, mas permite alertar se o mesmo pedido for ajustado de novo em outra hora
        id_unico = f"{pedido_id}_{data_ajuste_raw.split('.')[0]}"

        if id_unico not in enviados:
            status_regra = str(row.get('status_alerta', 'OK')).upper()
            
            # Formatação de Data
            try:
                dt_obj = datetime.strptime(data_ajuste_raw.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                data_exibicao = dt_obj.strftime('%d/%m/%Y %H:%M')
            except:
                data_exibicao = data_ajuste_raw.replace('T', ' ').split('.')[0]

            header = "*ALERTA DE AJUSTE CRÍTICO*" if "CRIT" in status_regra else "*NOTIFICAÇÃO DE AJUSTE DE PEDIDO*"
            status_line = f"*Status:* {'CRÍTICO' if 'CRIT' in status_regra else 'OK'}"

            msg_slack = {
                "text": (
                    f"{header}\n"
                    f"──────────────────────────────\n"
                    f"{status_line}\n"
                    f"*ID do Pedido:* {pedido_id}\n"
                    f"*Produto:* {row.get('product', 'N/A')}\n"
                    f"*Analista Responsável:* {row.get('analista', 'N/A')}\n"
                    f"*Percentual de Ajuste:* {formatar_valor(row.get('perc_ajuste'), '%')}\n"
                    f"*Valor do Ajuste:* {formatar_valor(row.get('valor_ajuste'), 'R$ ')}\n"
                    f"*Data do Evento:* {data_exibicao}\n"
                    f"──────────────────────────────"
                )
            }
            
            if requests.post(SLACK_WEBHOOK_URL, json=msg_slack).status_code == 200:
                registrar_envio(id_unico)
                print(f"Enviado: {pedido_id}")
                # Adicionamos ao set local para não repetir no mesmo loop
                enviados.add(id_unico)

if __name__ == "__main__":
    main()
