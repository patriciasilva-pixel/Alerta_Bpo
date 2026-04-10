import pandas as pd
from datetime import datetime
import requests
import os

# ===== CONFIG =====
URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

ARQUIVO_CONTROLE = "enviados.csv"

# ===== LER DADOS =====
df = pd.read_csv(URL)
df.columns = df.columns.str.lower().str.replace(" ", "_")

# ===== FILTROS =====
df = df[df['email'].str.contains('actionline', na=False)]

# ===== CRIAR ID ÚNICO =====
df['id_unico'] = (
    df['order_number'].astype(str) +
    df['product'].astype(str) +
    df['data_ajuste'].astype(str)
)

# ===== CARREGAR HISTÓRICO =====
try:
    enviados = pd.read_csv(ARQUIVO_CONTROLE)
    enviados_ids = set(enviados['id_unico'])
except:
    enviados_ids = set()

# ===== FILTRAR NOVOS =====
df_novos = df[~df['id_unico'].isin(enviados_ids)]

# ===== FORMATAR DATA =====
df_novos['data_ajuste'] = pd.to_datetime(
    df_novos['data_ajuste'],
    errors='coerce'
).dt.strftime('%d/%m/%Y %H:%M:%S')

# ===== ENVIAR PARA SLACK =====
novos_enviados = []

for _, row in df_novos.iterrows():

    mensagem = f"""
ALERTA BPO

Pedido: {row.get('order_number', 'N/A')}
Produto: {row.get('product', 'N/A')}
Analista: {row.get('analista', 'N/A')}
Ajuste (%): {row.get('perc_ajuste', 0)}
Data: {row.get('data_ajuste', 'N/A')}
"""

    requests.post(SLACK_WEBHOOK, json={"text": mensagem})

    novos_enviados.append(row['id_unico'])

# ===== SALVAR CONTROLE =====
if novos_enviados:
    df_salvar = pd.DataFrame({'id_unico': novos_enviados})

    try:
        antigos = pd.read_csv(ARQUIVO_CONTROLE)
        df_final = pd.concat([antigos, df_salvar])
    except:
        df_final = df_salvar

    df_final.drop_duplicates().to_csv(ARQUIVO_CONTROLE, index=False)
