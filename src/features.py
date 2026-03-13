import pandas as pd

def criar_features_resultado(df):
    """
    Features para o Cérebro de Resultado Final (Média de xG e ELO simulado).
    """
    df = df.copy()
    historico = {}
    
    medias_xg = []
    for index, row in df.iterrows():
        casa = row['time_casa']
        if casa not in historico: historico[casa] = []
        
        media = sum(historico[casa][-5:]) / len(historico[casa][-5:]) if historico[casa] else 0
        medias_xg.append(media)
        
        # Simulação: No mundo real, usaríamos o valor real de xG extraído
        historico[casa].append(row.get('casa_xg', row['gols_casa']))
        
    df['media_xg_casa_5j'] = medias_xg
    return df

def criar_features_taticas(df_jogadores):
    """
    Features para o Cérebro Tático (Média de Remates e Precisão).
    """
    if df_jogadores.empty: return df_jogadores
    
    df = df_jogadores.copy()
    df['precisao_remate'] = df['remates_baliza'] / df['remates_total']
    df['precisao_remate'] = df['precisao_remate'].fillna(0)
    
    # Médias por jogador seriam calculadas aqui num pipeline real
    return df

def criar_features_disciplinares(df_jogadores, arbitro_stats):
    """
    Features para o Cérebro Disciplinar (Agressividade e Rigor do Árbitro).
    """
    if df_jogadores.empty: return pd.DataFrame()
    
    # Agrupar faltas por time/jogo
    agressividade = df_jogadores.groupby('fixture_id')['faltas_cometidas'].sum().reset_index()
    # Adicionar dado do árbitro aqui
    return agressividade
