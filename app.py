import requests
import pandas as pd
import streamlit as st 

API_TOKEN = st.secrets["API_TOKEN"]

def get_deals():
    url = 'https://hyper3.pipedrive.com/api/v1/deals/'
    params = {
        'api_token': API_TOKEN,
        'limit': 100,  # Número máximo de itens por página
        'start': 0
    }
    all_deals = []
    print('Sending request...')

    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        deals_data = response.json()
        deals_list = deals_data.get('data', [])  # Garantir que deals_list seja uma lista
        if not deals_list:  # Se deals_list estiver vazio, usa lista vazia
            break
        all_deals.extend(deals_list)
        # Verifica se há mais páginas a serem buscadas
        if not deals_data['additional_data']['pagination']['more_items_in_collection']:
            break
        params['start'] += 100  # Avança para a próxima página

    return all_deals
