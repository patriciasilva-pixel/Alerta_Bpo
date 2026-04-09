import pandas as pd
from datetime import datetime

# ====== CONFIG ======
URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"

# ====== LER DADOS ======
df = pd.read_csv(URL)

# ====== PADRONIZAR COLUNAS ======
df.columns = df.columns.str.lower().str.replace(" ", "_")

# ====== FILTROS ======
# apenas usuários da Actionline
df = df[df['email'].str.contains('actionline', na=False)]

# apenas registros com ajuste de preço
df = df[df['valor_ajuste'] != 0]

# ====== TRATAMENTO DE DATA ======
df['data_ajuste'] = pd.to_datetime(
    df['data_ajuste'],
    errors='coerce'
).dt.strftime('%d/%m/%Y %H:%M:%S')

df['data_ajuste'] = df['data_ajuste'].fillna('Sem data')

# ====== ENVIO / PRINT ======
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

    print(mensagem)
