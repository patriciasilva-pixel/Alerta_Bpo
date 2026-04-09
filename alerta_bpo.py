import pandas as pd
import requests
import os

# ====== CONFIG ======
URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"
SLACK_WEBHOOK = "https://hooks.slack.com/services/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"
ARQUIVO = "enviados.csv"

# ====== LER DADOS ======
df = pd.read_csv(URL)

# ====== PADRONIZAR COLUNAS ======
df.columns = df.columns.str.lower().str.replace(" ", "_")

# ====== FILTROS ======
df = df[df['email'].str.contains('actionline', na=False)]
df = df[df['valor_ajuste'] != 0]

# ====== TRATAR DATA ======
df['data_ajuste'] = pd.to_datetime(df['data_ajuste'], errors='coerce')\
    .dt.strftime('%d/%m/%Y %H:%M:%S')

df['data_ajuste'] = df['data_ajuste'].fillna('Sem data')

# ====== HISTÓRICO ======
if os.path.exists(ARQUIVO):
    enviados = pd.read_csv(ARQUIVO)
    enviados_ids = set(enviados['id'])
else:
    enviados_ids = set()

novos_ids = []

# ====== ENVIO ======
for _, row in df.iterrows():

    id_unico = f"{row['order_number']}_{row['data_ajuste']}"

    if id_unico in enviados_ids:
        continue

    mensagem = f"""
ALERTA BPO - ATUALIZAÇÃO

Pedido: {row.get('order_number', 'N/A')}
Produto: {row.get('product', 'N/A')}
Analista: {row.get('analista', 'N/A')}
Nível: {row.get('nivel_alerta', 'N/A')}
Preço: R$ {row.get('preco_ajustado', 'N/A')}
Data: {row.get('data_ajuste', 'N/A')}
"""

    requests.post(SLACK_WEBHOOK, json={"text": mensagem})

    novos_ids.append(id_unico)

# ====== SALVAR HISTÓRICO ======
if novos_ids:
    df_novos = pd.DataFrame({'id': novos_ids})
    df_novos.to_csv(ARQUIVO, mode='a', header=not os.path.exists(ARQUIVO), index=False)
