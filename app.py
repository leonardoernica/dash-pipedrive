import requests
import pandas as pd
from datetime import datetime
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

@st.cache_data
def get_deals_df():
    logging.info('Iniciando a atualização dos dados...')
    deals = get_deals()
    df = create_funnel_df(deals)
    logging.info('Dados atualizados com sucesso!')
    return df

def safe_update_last_update():
    if 'last_update' not in st.session_state:
        st.session_state['last_update'] = datetime.now()
    else:
        st.session_state['last_update'] = datetime.now()
    logging.info(f"Dados atualizados em: {st.session_state['last_update']}")

def update_data():
    logging.info("Tentativa de atualização dos dados iniciada.")
    if 'data' not in st.session_state:
        logging.info("Nenhum dado pré-existente encontrado. Obtendo novos dados...")
        st.session_state['data'] = get_deals_df()
    else:
        logging.info("Atualizando dados existentes...")
        st.session_state['data'] = get_deals_df()
    safe_update_last_update()

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
                'pipeline_id': deal.get('pipeline_id')
            })
            total_seconds += duration
            current_date = end_date
    return pd.DataFrame(data)
