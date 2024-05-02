import requests
import pandas as pd
import streamlit as st 

API_TOKEN = st.secrets["API_TOKEN"]

def get_deal_details(deal_id):
    print('Iniciando Get Deal Details...')
    detail_url = f'https://hyper3.pipedrive.com/api/v1/deals/{deal_id}'
    params = {'api_token': API_TOKEN}
    response = requests.get(detail_url, params=params)
    response.raise_for_status()
    print('Finalizando Get Deal Details...')
    deal_data = response.json()['data']
    # Supondo que 'owner_name' possa ser extraído diretamente do detalhe do deal
    return deal_data

def get_deals():
    print('Iniciando Get Deals...')
    url = 'https://hyper3.pipedrive.com/api/v1/deals/'
    params = {
        'api_token': API_TOKEN,
        'limit': 100,  # Número máximo de itens por página
        'start': 0
    }
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
                'Owner Name': deal.get('owner_name', 'Unknown'),  # Garantindo que 'owner_name' seja capturado
                'pipeline_id': deal.get('pipeline_id')  # Garantindo que 'pipeline_id' seja capturado
            })
            total_seconds += duration
            current_date = end_date
    return pd.DataFrame(data)

def update_csv_with_new_data(df_new):
    if os.path.exists('deals.csv'):
        df_existing = pd.read_csv('deals.csv', parse_dates=['Start Date', 'End Date'])
    else:
        df_existing = pd.DataFrame(columns=df_new.columns)

    df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=['Deal ID', 'Stage ID'], keep='last')
    df_combined.to_csv('deals.csv', index=False)
    print('CSV atualizado com sucesso!')

deals = get_deals()
df_funnel = create_funnel_df(deals)
update_csv_with_new_data(df_funnel)
