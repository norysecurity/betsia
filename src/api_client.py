import requests
import pandas as pd
import os
from src.config import HEADERS, BASE_URL, LEAGUE_ID, SEASON

def coletar_dados_multimercado():
    print(f"Buscando dados REAIS da liga {LEAGUE_ID} temporada {SEASON} na API-Football...")
    url = f"{BASE_URL}/fixtures"
    querystring = {"league": str(LEAGUE_ID), "season": str(SEASON)}
    
    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        response.raise_for_status()
        dados = response.json().get('response', [])
        
        jogos = []
        for p in dados:
            if p['fixture']['status']['short'] != 'FT': continue
            
            # Extração básica inicial para o Cérebro 1 (Resultado Final)
            # Obs: Para Produção completa dos 3 cérebros, endpoints adicionais de odds e estatísticas serão chamados aqui.
            jogos.append({
                'id_jogo': p['fixture']['id'],
                'data': p['fixture']['date'],
                'time_casa': p['teams']['home']['name'],
                'time_fora': p['teams']['away']['name'],
                'gols_casa': p['goals']['home'],
                'gols_fora': p['goals']['away'],
                'resultado_casa': 1 if p['goals']['home'] > p['goals']['away'] else 0,
                # Features sintéticas temporárias para manter o pipeline rodando enquanto expandimos a API
                'xg_diff': p['goals']['home'] - p['goals']['away'], 
                'posse_ataque': 50.0,
                'odd_casa': 2.0, 
                'remates_over_2_5': 1 if p['goals']['home'] > 1 else 0,
                'odd_remates_over_2_5': 1.85,
                'cartoes_over_4_5': 1,
                'odd_cartoes_over_4_5': 1.90,
                'remates_p90': 3.0,
                'concessao_adv': 10.0,
                'media_arbitro': 5.0,
                'tensao': 5.0
            })
            
        df = pd.DataFrame(jogos)
        os.makedirs('data/raw', exist_ok=True)
        df.to_csv('data/raw/dados_reais_producao.csv', index=False)
        print(f"Sucesso! {len(df)} partidas reais processadas.")
        return df
    except Exception as e:
        print(f"Erro ao conectar com a API: {e}")
        return pd.DataFrame()
