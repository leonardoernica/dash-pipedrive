import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
# Supondo que app.py tenha a função get_deals original
from app import get_deals as original_get_deals

@st.cache_data
def get_deals():
    return original_get_deals()

data = get_deals()
df = pd.DataFrame(data)
# Conversão e extração de dados
df['add_time'] = pd.to_datetime(df['add_time'])
df['owner_name'] = df['user_id'].apply(lambda x: x['name'])

# Streamlit layout
st.title('Dashboard Comercial - Soluções Hyper')

# Default time period: last 7 days to today
default_start_date = datetime.now() - timedelta(days=7)
default_end_date = datetime.now()

# Sidebar - Date and owner filters
start_date = st.sidebar.date_input("Data Início", default_start_date)
end_date = st.sidebar.date_input("Data Fim", default_end_date)
owner_list = ['Todos'] + list(df['owner_name'].unique())
selected_owners = st.sidebar.multiselect('Selecione o Dono do Negócio', options=owner_list, default='Todos')

# Filter data based on dates and owner
if 'Todos' in selected_owners or not selected_owners:
    filtered_df = df[(df['pipeline_id'] == 1) & 
                     (df['status'] == 'open') & 
                     (df['add_time'].dt.date >= start_date) & 
                     (df['add_time'].dt.date <= end_date)]
else:
    filtered_df = df[(df['pipeline_id'] == 1) & 
                     (df['status'] == 'open') & 
                     (df['add_time'].dt.date >= start_date) & 
                     (df['add_time'].dt.date <= end_date) &
                     (df['owner_name'].isin(selected_owners))]

# Filter data based on dates and owner
if 'Todos' in selected_owners or not selected_owners:
    df_fat = df[(df['pipeline_id'] == 1) & 
                     (df['status'] == 'won') & 
                     (df['add_time'].dt.date >= start_date) & 
                     (df['add_time'].dt.date <= end_date)]
else:
    df_fat = df[(df['pipeline_id'] == 1) & 
                     (df['status'] == 'won') & 
                     (df['add_time'].dt.date >= start_date) & 
                     (df['add_time'].dt.date <= end_date) &
                     (df['owner_name'].isin(selected_owners))]

faturamento = df_fat.groupby(df_fat['add_time'].dt.date)['value'].sum()

# Criação do gráfico de linha para faturamento
fig_faturamento = px.line(
    x=faturamento.index,  # Utilizar o índice do grupo para o eixo X
    y=faturamento.values,  # Utilizar os valores do grupo para o eixo Y
    labels={'x': 'Data', 'y': 'Faturamento'},
    title='Faturamento'
)
fig_faturamento.update_xaxes(tickformat="%d/%m/%Y")
fig_faturamento.update_layout(xaxis_title="Data", yaxis_title="Faturamento (R$)")

# Metrics
nao_iniciados = len(filtered_df[filtered_df['stage_id'] == 1])
iniciados = len(filtered_df[filtered_df['stage_id'] == 2])
agendados = len(filtered_df[filtered_df['stage_id'] == 3])
propostas = len(filtered_df[filtered_df['stage_id'] == 5])
negociacao = len(filtered_df[filtered_df['stage_id'] == 6])
fechamento = len(filtered_df[filtered_df['stage_id'] == 7])

# Creating interactive bar chart with Plotly
data = {'Status': ['Iniciados', 'Agendados', 'Propostas', 'Negociações', 'Fechamentos'],
        'Quantidade': [iniciados, agendados, propostas, negociacao, fechamento]}
fig = px.bar(data, x='Status', y='Quantidade', text='Quantidade')
fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_title="Status", yaxis_title="Quantidade")


# Mostrar o gráfico no Streamlit
# Faturamento total do intervalo filtrado
faturamento_total = faturamento.sum()
st.write(f"Faturamento Total: R$ {faturamento_total:,.2f}")
st.plotly_chart(fig_faturamento, use_container_width=True)
st.plotly_chart(fig, use_container_width=True)