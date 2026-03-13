import requests
import pandas as pd
from src.config import HEADERS, BASE_URL

def coletar_jogos(league_id, season_year):
    """
    Coleta dados de partidas finalizadas da API-Football.
    """
    url = f"{BASE_URL}/fixtures"
    querystring = {"league": str(league_id), "season": str(season_year)}
    
    response = requests.get(url, headers=HEADERS, params=querystring)
    response.raise_for_status()
    dados = response.json().get('response', [])
    
    jogos = []
    for p in dados:
        # Filtra apenas jogos que já terminaram
        if p['fixture']['status']['short'] != 'FT': continue
        
        jogos.append({
            'data': p['fixture']['date'],
            'time_casa': p['teams']['home']['name'],
            'time_fora': p['teams']['away']['name'],
            'gols_casa': p['goals']['home'],
            'gols_fora': p['goals']['away'],
            'resultado_casa': 1 if p['goals']['home'] > p['goals']['away'] else 0
        })
    
    df = pd.DataFrame(jogos)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        return df.sort_values('data').reset_index(drop=True)
    return df
