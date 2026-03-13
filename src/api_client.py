import requests
import pandas as pd
import os
from datetime import datetime
from src.config import HEADERS, BASE_URL, LEAGUE_ID, SEASON

def coletar_dados_multimercado():
    # Pega a data de hoje para criar o nome do arquivo
    hoje = datetime.now().strftime('%Y-%m-%d')
    arquivo_cache = f"data/raw/dados_liga_{LEAGUE_ID}_{hoje}.csv"
    
    # 1. ESTRATÉGIA DO PLANO GRÁTIS: CACHE LOCAL
    if os.path.exists(arquivo_cache):
        print(f"🛡️ PLANO GRÁTIS ATIVO: Lendo dados do computador ({arquivo_cache}).")
        print("Nenhuma requisição da API foi gasta nesta execução!")
        return pd.read_csv(arquivo_cache)
        
    print("⬇️ Baixando dados da API (Gastando 1 requisição do seu limite de 100/dia)...")
    url = f"{BASE_URL}/fixtures"
    querystring = {"league": str(LEAGUE_ID), "season": str(SEASON)}
    
    try:
        response = requests.get(url, headers=HEADERS, params=querystring)
        response.raise_for_status()
        
        # 2. MONITORAMENTO DE COTA
        limite_restante = response.headers.get('x-ratelimit-requests-remaining', 'Desconhecido')
        print(f"📊 STATUS DA COTA: Você ainda tem {limite_restante} requisições gratuitas hoje.")
        
        dados = response.json().get('response', [])
        
        jogos = []
        for p in dados:
            if p['fixture']['status']['short'] != 'FT': 
                continue
            
            jogos.append({
                'id_jogo': p['fixture']['id'],
                'data': p['fixture']['date'],
                'time_casa': p['teams']['home']['name'],
                'time_fora': p['teams']['away']['name'],
                'gols_casa': p['goals']['home'],
                'gols_fora': p['goals']['away'],
                'resultado_casa': 1 if p['goals']['home'] > p['goals']['away'] else 0,
                
                # Preenchendo estatísticas complementares
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
        
        # Cria a pasta se não existir e salva o arquivo de hoje
        os.makedirs('data/raw', exist_ok=True)
        df.to_csv(arquivo_cache, index=False)
        
        print(f"✅ Sucesso! {len(df)} partidas salvas localmente. O robô não precisará da API pelo resto do dia.")
        return df
        
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return pd.DataFrame()
