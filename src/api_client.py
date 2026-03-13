import requests
import pandas as pd
import os
import numpy as np
from datetime import datetime
from src.config import HEADERS, BASE_URL, LEAGUE_ID, SEASON

def coletar_dados_api():
    hoje = datetime.now().strftime('%Y-%m-%d')
    arquivo_cache = f"data/raw/dados_completos_{LEAGUE_ID}_{hoje}.csv"
    
    # Verifica diretório
    os.makedirs('data/raw', exist_ok=True)
    
    if os.path.exists(arquivo_cache):
        print("🛡️ CACHE ATIVO: Lendo dados locais sem gastar requisições da API.")
        return pd.read_csv(arquivo_cache)
        
    print("⬇️ Buscando dados oficiais da API-Sports...")
    url = f"{BASE_URL}/fixtures"
    querystring = {"league": str(LEAGUE_ID), "season": str(SEASON)}
    
    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        response.raise_for_status()
        dados = response.json().get('response', [])
        
        jogos = []
        for p in dados:
            status = p['fixture']['status']['short']
            if status not in ['FT', 'NS']: continue # Pega apenas Encerrados e Não Iniciados
            
            jogos.append({
                'id_jogo': p['fixture']['id'],
                'data': p['fixture']['date'],
                'status': status,
                'time_casa': p['teams']['home']['name'],
                'time_fora': p['teams']['away']['name'],
                'gols_casa': p['goals']['home'] if status == 'FT' else 0,
                'gols_fora': p['goals']['away'] if status == 'FT' else 0,
                'resultado_casa': 1 if status == 'FT' and p['goals']['home'] > p['goals']['away'] else 0,
                
                # Dados simulados para estruturar a pipeline
                'xg_diff': np.random.uniform(-1, 2) if status == 'NS' else (p['goals']['home'] - p['goals']['away']),
                'posse_ataque': np.random.uniform(30, 70),
                'odd_casa': round(np.random.uniform(1.5, 3.5), 2), 
                'remates_over_2_5': 1 if status == 'FT' and p['goals']['home'] > 1 else 0,
                'odd_remates_over_2_5': round(np.random.uniform(1.5, 2.5), 2),
                'cartoes_over_4_5': 1 if status == 'FT' and np.random.rand() > 0.5 else 0,
                'odd_cartoes_over_4_5': round(np.random.uniform(1.6, 2.8), 2),
                'remates_p90': np.random.uniform(2, 5),
                'concessao_adv': np.random.uniform(8, 15),
                'media_arbitro': np.random.uniform(3, 7),
                'tensao': np.random.uniform(2, 9)
            })
            
        df = pd.DataFrame(jogos)
        df.to_csv(arquivo_cache, index=False)
        print(f"✅ Sucesso! {len(df)} partidas salvas.")
        return df
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return pd.DataFrame()
