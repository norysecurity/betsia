import requests
import pandas as pd
import os
from src.config import HEADERS, BASE_URL

def coletar_jogos(league_id, season_year):
    """
    Coleta dados básicos de partidas finalizadas (vence/perde/empata).
    """
    url = f"{BASE_URL}/fixtures"
    querystring = {"league": str(league_id), "season": str(season_year)}
    
    response = requests.get(url, headers=HEADERS, params=querystring)
    response.raise_for_status()
    dados = response.json().get('response', [])
    
    jogos = []
    for p in dados:
        if p['fixture']['status']['short'] != 'FT': continue
        
        jogos.append({
            'fixture_id': p['fixture']['id'],
            'data': p['fixture']['date'],
            'time_casa': p['teams']['home']['name'],
            'time_fora': p['teams']['away']['name'],
            'gols_casa': p['goals']['home'],
            'gols_fora': p['goals']['away'],
            'resultado_casa': 1 if p['goals']['home'] > p['goals']['away'] else 0,
            'arbitro': p['fixture'].get('referee', 'Desconhecido')
        })
    
    df = pd.DataFrame(jogos)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
        return df.sort_values('data').reset_index(drop=True)
    return df

def extrair_detalhes_profundos(fixture_id):
    """
    Extrai métricas detalhadas (Remates, Faltas, Passes) para os cérebros Tático e Disciplinar.
    """
    url_players = f"{BASE_URL}/fixtures/players"
    querystring_players = {"fixture": str(fixture_id)}
    
    try:
        response = requests.get(url_players, headers=HEADERS, params=querystring_players)
        response.raise_for_status()
        dados_players = response.json().get('response', [])
        
        lista_stats = []
        for equipa in dados_players:
            nome_equipa = equipa['team']['name']
            for jogador in equipa['players']:
                stats = jogador['statistics'][0]
                lista_stats.append({
                    'fixture_id': fixture_id,
                    'equipa': nome_equipa,
                    'jogador': jogador['player']['name'],
                    'minutos': stats['games'].get('minutes') or 0,
                    'remates_total': stats['shots'].get('total') or 0,
                    'remates_baliza': stats['shots'].get('on') or 0,
                    'faltas_cometidas': stats['fouls'].get('committed') or 0,
                    'cartoes_amarelos': stats['cards'].get('yellow') or 0
                })
        
        return pd.DataFrame(lista_stats)
    except Exception as e:
        print(f"Erro ao extrair detalhes do jogo {fixture_id}: {e}")
        return pd.DataFrame()

def extrair_stats_equipa(fixture_id):
    """
    Extrai xG e Posse de bola para o cérebro de Resultado Final.
    """
    url_stats = f"{BASE_URL}/fixtures/statistics"
    querystring = {"fixture": str(fixture_id)}
    
    try:
        response = requests.get(url_stats, headers=HEADERS, params=querystring)
        response.raise_for_status()
        dados = response.json().get('response', [])
        
        stats_jogo = {'fixture_id': fixture_id}
        for s in dados:
            prefixo = 'casa_' if s == dados[0] else 'fora_'
            for item in s['statistics']:
                if item['type'] == 'Expected Goals':
                    stats_jogo[f'{prefixo}xg'] = float(item['value']) if item['value'] else 0.0
                if item['type'] == 'Ball Possession':
                    stats_jogo[f'{prefixo}posse'] = int(str(item['value']).replace('%','')) if item['value'] else 0
        
        return stats_jogo
    except Exception as e:
        return {'fixture_id': fixture_id, 'casa_xg': 0, 'fora_xg': 0, 'casa_posse': 50, 'fora_posse': 50}
