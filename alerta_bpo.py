import pandas as pd
from datetime import datetime

# ====== LER CSV ======
URL = "https://cayena.metabaseapp.com/public/question/9015cb16-054a-421d-b979-ff20aa139708.csv"

df = pd.read_csv(URL)

# ====== PADRONIZAR COLUNAS ======
df.columns = df.columns.str.lower().str.replace(" ", "_")

# ====== FILTROS ======
# apenas actionline
df = df[df['email'].str.contains('actionline', na=False)]

# apenas ajustes reais (evita pegar item sem alteração de preço)
df = df[df['valor_ajuste'] != 0]

# ====== TRATAR DATA (ANTI ERRO TOTAL) ======
df['data_ajuste'] = pd.to_datetime(
    df['data_ajuste'],
    errors='coerce'
)

df['data_ajuste'] = df['data_ajuste'].dt.strftime('%d/%m/%Y %H:%M:%S')

# se tiver algum NaN vira vazio (não quebra o slack)
df['data_ajuste'] = df['data_ajuste'].fillna('Sem data')

# ====== EXEMPLO DE USO (PRINT OU SLACK) ======
for _, row in df.iterrows():
    mensagem = f"""
🚨 ALERTA BPO

Pedido: {row.get('order_number', 'N/A')}
Produto: {row.get('product', 'N/A')}
Analista: {row.get('analista', 'N/A')}
Email: {row.get('email', 'N/A')}
Ajuste: {row.get('perc_ajuste', 0)}%
Data: {row.get('data_ajuste', 'N/A')}
"""

    print(mensagem)
