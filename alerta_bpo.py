import pandas as pd
from datetime import datetime
import requests
import os

# ====== CONFIG ======
URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

# ====== LER DADOS ======
df = pd.read_csv(URL)

# ====== PADRONIZAR COLUNAS ======
df.columns = df.columns.str.lower().str.replace(" ", "_")

# ====== FILTROS ======
df = df[df['email'].str.contains('actionline', na=False)]
df = df[df['valor_ajuste'] != 0]

# ====== DATA ======
df['data_ajuste'] = pd.to_datetime(df['data_ajuste'], errors='coerce')
df['data_ajuste'] = df['data_ajuste'].dt.strftime('%d/%m/%Y %H:%M:%S')
df['data_ajuste'] = df['data_ajuste'].fillna('Sem data')

# ====== ENVIO PARA SLACK ======
for _, row in df.iterrows():

    mensagem = f"""
ALERTA BPO

Pedido: {row.get('order_number', 'N/A')}
Produto: {row.get('product', 'N/A')}
Analista: {row.get('analista', 'N/A')}
Email: {row.get('email', 'N/A')}
Ajuste (%): {row.get('perc_ajuste', 0)}
Data: {row.get('data_ajuste', 'N/A')}
"""

    payload = {"text": mensagem}

    requests.post(SLACK_WEBHOOK, json=payload)
