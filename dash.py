import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app import update_deals_csv

def load_data():
    try:
        data = pd.read_csv('deals.csv', parse_dates=['Start Date', 'End Date'])
        if data.empty:
            return None  # Retorna None se o arquivo estiver vazio
        data['Owner Name'] = data['Owner Name'].fillna('Unknown').astype(str)
        return data
    except FileNotFoundError:
        st.error("O arquivo deals.csv não foi encontrado.")
        return None  # Retorna None se o arquivo não existir
    except pd.errors.EmptyDataError:
        return None  # Retorna None se o arquivo estiver completamente vazio

st.title('Dashboard Comercial - Soluções Hyper')

# Inicializa o agendador
scheduler = BackgroundScheduler()
scheduler.add_job(update_deals_csv, 'interval', hours=1)
scheduler.start()

# Loop para aguardar até que o arquivo não esteja vazio
while True:
    df = load_data()
    if df is not None:
        break
    else:
        st.warning("Aguardando dados... Atualizando em 30 segundos.")
        time.sleep(30)  # Espera 30 segundos antes de verificar novamente

@st.cache_data(ttl=4000, allow_output_mutation=True)
def get_cached_data():
    return df  # Usa o DataFrame carregado após a verificação

df = get_cached_data()

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
        # Adicionando garantia de representação de todos os Stages, mesmo que seja zero
        all_stages = pd.DataFrame({'Stage ID': range(1, 8), 'Count': [0]*7})  # Adapte conforme o número de Stages
        stage_counts = funnel_df['Stage ID'].value_counts().reset_index()
        stage_counts.columns = ['Stage ID', 'Count']
        stage_counts = pd.merge(all_stages, stage_counts, on='Stage ID', how='left').fillna(0)
        stage_counts['Count'] = stage_counts['Count_y']
        fig_funnel = px.funnel(stage_counts, x='Count', y='Stage ID', orientation='h', title='Funil de Vendas por Stage ID')
        fig_funnel.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_funnel, use_container_width=True)
