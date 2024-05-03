import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from app import update_data

st.title('Dashboard Comercial - Soluções Hyper')

update_data()

def get_cached_data():
    return st.session_state['data'] if 'data' in st.session_state else pd.DataFrame()

df = get_cached_data()

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
        st.write("Nenhum resultado encontrado para os filtros aplicados.")
    else:
        filtered_df = filtered_df.sort_values(by='End Date').drop_duplicates(subset=['Deal ID'], keep='last')
        faturamento = filtered_df.groupby(filtered_df['End Date'].dt.date)['Value'].sum()
        if not faturamento.empty:
            fig_faturamento = px.line(
                x=faturamento.index, y=faturamento.values,
                labels={'x': 'Data', 'y': 'Faturamento'}, title='Faturamento'
            )
            fig_faturamento.update_xaxes(tickformat="%d/%m/%Y")
            fig_faturamento.update_layout(xaxis_title="Data", yaxis_title="Faturamento (R$)")
            st.write(f"Faturamento Total: R$ {faturamento.sum():,.2f}")
            st.plotly_chart(fig_faturamento, use_container_width=True)
        else:
            st.write("Nenhum faturamento para mostrar nos filtros selecionados.")

        funnel_df = df[(df['pipeline_id']==1) &
                       (df['Start Date'].dt.date >= start_date) & 
                       (df['Start Date'].dt.date <= end_date) &
                       ((df['Owner Name'].isin(selected_owners)) if 'Todos' not in selected_owners else True)]
        
        if not funnel_df.empty:
            stage_counts = funnel_df['Stage ID'].value_counts().reset_index()
            stage_counts.columns = ['Stage ID', 'Count']
            stage_counts = stage_counts.sort_values(by='Stage ID')
            fig_funnel = px.funnel(stage_counts, x='Count', y='Stage ID', orientation='h', title='Funil de Vendas por Stage ID')
            fig_funnel.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_funnel, use_container_width=True)
        else:
            st.write("Nenhum dado no funil para mostrar nos filtros selecionados.")
