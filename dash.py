import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from app import update_data

st.title('Dashboard Comercial - Soluções Hyper')

# Menu de navegação
menu = ["Dashboard", "Relatório Motivos de Perda"]
choice = st.sidebar.selectbox("Selecione a Página", menu)

update_data()

def get_cached_data():
    return st.session_state['data'] if 'data' in st.session_state else pd.DataFrame()

df = get_cached_data()

stage_names = {
    '1': 'Primeiro Contato',
    '2': 'Prospecção',
    '3': 'Diagnóstico',
    '4': 'Avaliação Técnica',
    '5': 'Proposta',
    '6': 'Negociação',
    '7': 'Fechamento'
}

if 'last_update' in st.session_state:
    st.write(f"Última atualização dos dados: {st.session_state['last_update']}")

if choice == "Dashboard":
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
            # Assegure-se que estamos agrupando corretamente e visualizando o gráfico corretamente
            if not filtered_df.empty:
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

        # Verificando e exibindo dados do funil
        funnel_df = df[(df['pipeline_id']==1) &
                    (df['Start Date'].dt.date >= start_date) & 
                    (df['Start Date'].dt.date <= end_date) &
                    ((df['Owner Name'].isin(selected_owners)) if 'Todos' not in selected_owners else True)]
        
        if funnel_df.empty:
            st.write("Nenhum resultado encontrado para os filtros aplicados.")
        else:
            stage_order = ['Primeiro Contato', 'Prospecção', 'Diagnóstico', 'Avaliação Técnica', 'Proposta', 'Negociação', 'Fechamento']
            stage_counts = funnel_df['Stage ID'].value_counts().reset_index()
            stage_counts.columns = ['Stage ID', 'Count']
            stage_counts = stage_counts.sort_values(by='Stage ID')

            # Mapeando Stage ID para nomes das etapas
            stage_counts['Stage Name'] = stage_counts['Stage ID'].map(stage_names)

            stage_counts['Stage Name'] = pd.Categorical(stage_counts['Stage Name'], categories=stage_order, ordered=True)
            fig_funnel = px.funnel(stage_counts, x='Count', y='Stage Name', orientation='h', title='Funil de Vendas por Etapa do Funil')
            fig_funnel.update_layout(yaxis={'categoryorder':'array', 'categoryarray': stage_order})
            st.plotly_chart(fig_funnel, use_container_width=True)

elif choice == "Relatório Motivos de Perda":
    st.header("Relatório Motivos de Perda")
    if not df.empty:
        # Filtros para a página "Relatório Motivos de Perda"
        st.sidebar.header("Filtros")

        df = df[(df['pipeline_id'] == 1)]

        default_start_date = datetime.now() - timedelta(days=30)
        default_end_date = datetime.now()
        start_date = st.sidebar.date_input("Data Início", default_start_date)
        end_date = st.sidebar.date_input("Data Fim", default_end_date)
        owner_list = ['Todos'] + sorted(df['Owner Name'].unique())
        selected_owners = st.sidebar.multiselect('Selecione o Dono do Negócio', owner_list, default='Todos')
        all_stage_names = ['Todos'] + list(stage_names.values())  # Adicionar "Todos" no início
        selected_stage_names = st.sidebar.multiselect('Selecione a Etapa de Funil', all_stage_names, default='Todos')

        # Manter apenas o último estágio de cada Deal ID
        df = df.sort_values(by=['Deal ID', 'Stage ID']).drop_duplicates(subset=['Deal ID'], keep='last')

        filtered_df = df[(df['Status'] == 'lost') &
                        (df['End Date'].dt.date >= start_date) &
                        (df['End Date'].dt.date <= end_date) &
                        ((df['Owner Name'].isin(selected_owners)) if 'Todos' not in selected_owners else True) &
                        ((df['Stage ID'].isin([stage_id for stage_id, name in stage_names.items()
                                                if name in selected_stage_names and name != 'Todos']))
                        if 'Todos' not in selected_stage_names else True)]
        # Contar os motivos de perda apenas uma vez por Deal ID
        if not filtered_df.empty:
            lost_reasons = filtered_df.groupby('lost_reason')['lost_reason'].count().reset_index(name='Count')
            lost_reasons = lost_reasons.sort_values(by='Count', ascending=False)
            st.write(f"Total de Negócios Perdidos: {lost_reasons['Count'].sum()}")
            fig_lost_reasons = px.bar(
                lost_reasons, x='lost_reason', y='Count',
                labels={'lost_reason': 'Motivo de Perda', 'Count': 'Quantidade'}, title='Motivos de Perda de Negócios'
            )
            fig_lost_reasons.update_layout(xaxis_title="Motivo de Perda", yaxis_title="Quantidade")
            st.plotly_chart(fig_lost_reasons, use_container_width=True)
        else:
            st.write("Nenhum resultado encontrado para os filtros aplicados.")
    else:
        st.write("Nenhum dado disponível.")
