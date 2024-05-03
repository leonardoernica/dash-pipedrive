import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from app import update_data

# Inicialização segura das chaves do session_state
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()
if 'last_update' not in st.session_state:
    st.session_state['last_update'] = datetime.now()
    
st.title('Dashboard Comercial - Soluções Hyper')

scheduler = BackgroundScheduler(timezone=pytz.timezone('America/Sao_Paulo'))

def scheduled_job():
    print(f"Executando o trabalho agendado em: {datetime.now(pytz.timezone('America/Sao_Paulo'))}")
    update_data()

scheduler.add_job(scheduled_job, 'interval', minutes=40, next_run_time=datetime.now())
scheduler.start()

# Para manter o script rodando
import time
try:
    while True:
        time.sleep(2)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()

# Função para obter dados da memória
def get_cached_data():
    return st.session_state['data'] if 'data' in st.session_state else pd.DataFrame()

df = get_cached_data()

# Mostrando o horário da última atualização
if 'last_update' in st.session_state:
    st.write(f"Última atualização dos dados: {st.session_state['last_update']}")

if df.empty:
    st.write("Nenhum dado disponível para exibir.")
else:
    default_start_date = datetime.now() - timedelta(days=7)
    default_end_date = datetime.now()
    start_date = st.sidebar.date_input("Data Início", default_start_date)
    end_date = st.sidebar.date_input("Data Fim", default_end_date)
    owner_list = ['Todos'] + sorted(df['Owner Name'].unique())
    selected_owners = st.sidebar.multiselect('Selecione o Dono do Negócio', owner_list, default='Todos')

    filtered_df = df[(df['Status'] == 'won') & 
                     (df['End Date'].dt.date >= start_date) & 
                     (df['End Date'].dt.date <= end_date) &
                     ((df['Owner Name'].isin(selected_owners)) if 'Todos' not in selected_owners else True)]

    if filtered_df.empty:
        st.write("Sem resultados para esta pesquisa.")
    else:
        faturamento = filtered_df.groupby(filtered_df['End Date'].dt.date)['Value'].sum()
        fig_faturamento = px.line(
            x=faturamento.index, y=faturamento.values,
            labels={'x': 'Data', 'y': 'Faturamento'}, title='Faturamento'
        )
        fig_faturamento.update_xaxes(tickformat="%d/%m/%Y")
        fig_faturamento.update_layout(xaxis_title="Data", yaxis_title="Faturamento (R$)")
        st.write(f"Faturamento Total: R$ {faturamento.sum():,.2f}")
        st.plotly_chart(fig_faturamento, use_container_width=True)

    funnel_df = df[(df['pipeline_id']==1) &
                   (df['Start Date'].dt.date >= start_date) & 
                   (df['Start Date'].dt.date <= end_date) &
                   ((df['Owner Name'].isin(selected_owners)) if 'Todos' not in selected_owners else True)]

    if funnel_df.empty:
        st.write("Sem dados no funil para esta pesquisa.")
    else:
        all_stages = pd.DataFrame({'Stage ID': range(1, 8), 'Count': [0]*7})
        stage_counts = funnel_df['Stage ID'].value_counts().reset_index()
        stage_counts.columns = ['Stage ID', 'Count']
        stage_counts = pd.merge(all_stages, stage_counts, on='Stage ID', how='left').fillna(0)
        stage_counts['Count'] = stage_counts['Count_y']
        fig_funnel = px.funnel(stage_counts, x='Count', y='Stage ID', orientation='h', title='Funil de Vendas por Stage ID')
        fig_funnel.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_funnel, use_container_width=True)
