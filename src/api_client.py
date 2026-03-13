import requests
import pandas as pd
import os
import numpy as np
from datetime import datetime
from src.config import ODDS_API_KEY

def coletar_dados_api(force_refresh=False):
    hoje = datetime.now().strftime('%Y-%m-%d')
    arquivo_cache = f"data/raw/dados_oddsapi_{hoje}.csv"
    os.makedirs('data/raw', exist_ok=True)
    
    if os.path.exists(arquivo_cache) and not force_refresh:
        print("🛡️ CACHE ATIVO: A ler jogos já guardados hoje.")
        return pd.read_csv(arquivo_cache)
        
    print("📡 A ligar à The Odds API para varredura Global (Brasil + Europa)...")
    
    if not ODDS_API_KEY or ODDS_API_KEY == 'cole_a_sua_chave_da_odds_api_aqui':
        print("❌ ERRO: Chave ODDS_API_KEY não configurada.")
        return pd.DataFrame()

    # 1. RADAR INTELIGENTE: Procurar todas as ligas ativas
    url_sports = "https://api.the-odds-api.com/v4/sports"
    try:
        res_sports = requests.get(url_sports, params={'apiKey': ODDS_API_KEY})
        res_sports.raise_for_status()
        active_sports = res_sports.json()
    except Exception as e:
        print(f"❌ Erro ao buscar lista de desportos: {e}")
        return pd.DataFrame()

    ligas_para_varrer = []
    # Expandido para incluir as principais ligas do mundo
    palavras_chave_alvo = [
        'brazil', 'brasil', 'paulista', 'carioca', 'mineiro', 'gaucho', 'libertadores', 'sulamericana', 
        'spain_la_liga', 'england_premier', 'germany_bundesliga', 'italy_serie_a', 'france_ligue_1',
        'uefa_champs', 'uefa_europa'
    ]
    
    for sport in active_sports:
        key_lower = sport['key'].lower()
        title_lower = sport['title'].lower()
        
        if any(palavra in key_lower or palavra in title_lower for palavra in palavras_chave_alvo):
            ligas_para_varrer.append(sport['key'])
            print(f"🎯 Encontrado Campeonato Alvo: {sport['title']} ({sport['key']})")

    if not ligas_para_varrer:
        print("⚠️ Nenhuma liga alvo encontrada. Usando fallback de segurança...")
        ligas_para_varrer = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_italy_serie_a']

    jogos = []
    
    # 2. VARREDURA DE ODDS E CASAS DE APOSTAS
    for liga in ligas_para_varrer:
        print(f"🔎 A extrair jogos e odds da liga: {liga}...")
        url_odds = f"https://api.the-odds-api.com/v4/sports/{liga}/odds"
        params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'eu,uk,us', 
            'markets': 'h2h'
        }
        
        try:
            response = requests.get(url_odds, params=params)
            if response.status_code != 200:
                continue
                
            dados = response.json()
            
            for ev in dados:
                odd_casa_real = 0.0 
                nome_casa_aposta = "Desconhecida"
                bookmakers = ev.get('bookmakers', [])
                
                if bookmakers:
                    # Tenta a Bet365 primeiro
                    bookmaker_data = next((b for b in bookmakers if b['key'] == 'bet365'), bookmakers[0])
                    nome_casa_aposta = bookmaker_data.get('title', 'Casa Desconhecida')
                    
                    markets = bookmaker_data.get('markets', [])
                    h2h_market = next((m for m in markets if m['key'] == 'h2h'), None)
                    
                    if h2h_market:
                        outcomes = h2h_market.get('outcomes', [])
                        if outcomes:
                            # Procura o outcome do time da casa pelo nome
                            casa_outcome = next((o for o in outcomes if o['name'] == ev['home_team']), outcomes[0])
                            odd_casa_real = casa_outcome.get('price', 0.0)
                
                if odd_casa_real == 0.0:
                    continue 
                    
                jogos.append({
                    'id_jogo': ev['id'],
                    'data': hoje,
                    'status': 'NS', 
                    'time_casa': ev['home_team'],
                    'time_fora': ev['away_team'],
                    'gols_casa': 0,
                    'gols_fora': 0,
                    'resultado_casa': 0,
                    'btts_sim': 0, # Target 1 se ambos marcarem
                    'vencer_e_btts': 0, # Target 1 se casa vencer e ambos marcarem
                    'casa_de_aposta': nome_casa_aposta,
                    'xg_diff': np.random.uniform(-1.5, 2.5),
                    'posse_ataque': np.random.uniform(35, 65),
                    'odd_casa': odd_casa_real, 
                    'odd_btts_yes': round(np.random.uniform(1.6, 2.1), 2),
                    'odd_vencer_e_btts': round(odd_casa_real * np.random.uniform(1.8, 2.5), 2), # Odd combo
                    'remates_over_2_5': 0,
                    'odd_remates_over_2_5': round(np.random.uniform(1.5, 2.2), 2),
                    'cartoes_over_4_5': 0,
                    'odd_cartoes_over_4_5': round(np.random.uniform(1.7, 2.6), 2),
                    'remates_p90': np.random.uniform(1.5, 4.5),
                    'concessao_adv': np.random.uniform(9, 16),
                    'media_arbitro': np.random.uniform(3.5, 6.5),
                    'tensao': np.random.uniform(3, 9)
                })
        except Exception as e:
            print(f"❌ Erro na liga {liga}: {e}")
            
    df_futuro = pd.DataFrame(jogos)
    
    if df_futuro.empty:
        return pd.DataFrame()

    # Para simular histórico em um bot puramente de Odds API, clonamos os jogos como se tivessem ocorrido
    df_treino = df_futuro.copy()
    df_treino['status'] = 'FT'
    df_treino['resultado_casa'] = np.random.randint(0, 2, size=len(df_treino))
    df_treino['btts_sim'] = np.random.randint(0, 2, size=len(df_treino))
    df_treino['vencer_e_btts'] = (df_treino['resultado_casa'] & df_treino['btts_sim'])
    
    df_final = pd.concat([df_treino, df_futuro], ignore_index=True)
    df_final.to_csv(arquivo_cache, index=False)
    
    print(f"✅ Sucesso Radar Global! {len(df_futuro)} jogos extraídos.")
    return df_final
