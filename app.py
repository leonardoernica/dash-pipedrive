import requests
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import logging

# Configurando o logging
logging.basicConfig(level=logging.INFO)

API_TOKEN = st.secrets["API_TOKEN"]

def get_deal_details(deal_id):
    print('Iniciando Get Deal Details...')
    detail_url = f'https://hyper3.pipedrive.com/api/v1/deals/{deal_id}'
    params = {'api_token': API_TOKEN}
    response = requests.get(detail_url, params=params)
    response.raise_for_status()
    print('Finalizando Get Deal Details...')
    return response.json()['data']

def get_deals():
    print('Iniciando Get Deals...')
    url = 'https://hyper3.pipedrive.com/api/v1/deals/'
    params = {'api_token': API_TOKEN, 'limit': 100, 'start': 0}
    all_deals = []

    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        deals_data = response.json()
        deals_list = deals_data.get('data', [])
        if not deals_list:
            break

        print('Iniciando Get Deals Details de todos os Deals...')
        for deal in deals_list:
            detailed_deal = get_deal_details(deal['id'])
            all_deals.append(detailed_deal)

        if not deals_data['additional_data']['pagination']['more_items_in_collection']:
            break
        params['start'] += 100

    return all_deals

@st.cache_resource
def get_deals_df():
    last_update = st.session_state.get('last_update_time', None)
    current_time = datetime.now()

    # Atualizar somente se passou mais de 1 hora desde a última atualização
    if last_update is None or (current_time - last_update > timedelta(hours=1)):
        logging.info('Atualizando dados...')
        deals = get_deals()
        df = create_funnel_df(deals)
        st.session_state['last_update_time'] = current_time  # Atualiza o horário da última atualização
        logging.info('Dados atualizados com sucesso!')
        return df
    else:
        logging.info('Utilizando cache de dados...')
        return st.session_state.get('data', pd.DataFrame())  # Assegura que retorna um DataFrame vazio se 'data' não estiver definido

def update_data():
    # Essa função agora apenas chama o get_deals_df que decide se deve atualizar ou não
    st.session_state['data'] = get_deals_df()
    safe_update_last_update()

def safe_update_last_update():
    if 'last_update' not in st.session_state:
        st.session_state['last_update'] = datetime.now()
    else:
        st.session_state['last_update'] = datetime.now()
    logging.info(f"Dados atualizados em: {st.session_state['last_update']}")

def create_funnel_df(deals):
    print('Iniciando Data Frame...')
    data = []
    for deal in deals:
        creation_date = pd.to_datetime(deal['add_time'])
        stage_times = deal['stay_in_pipeline_stages']['times_in_stages']
        current_date = creation_date
        total_seconds = 0
        for stage_id, duration in stage_times.items():
            end_date = creation_date + pd.to_timedelta(total_seconds + duration, unit='s')
            data.append({
                'Deal ID': deal['id'],
                'Stage ID': stage_id,
                'Start Date': current_date,
                'End Date': end_date,
                'Value': deal['value'],
                'Status': deal['status'],
                'Owner Name': deal.get('owner_name', 'Unknown'),
                'pipeline_id': deal.get('pipeline_id'),
                'lost_reason': deal.get('lost_reason', "") 
            })
            total_seconds += duration
            current_date = end_date
    return pd.DataFrame(data)
