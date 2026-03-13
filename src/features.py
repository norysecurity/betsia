import pandas as pd

def criar_features(df):
    """
    Cria atributos para o modelo: médias móveis de gols feitos e sofridos nos últimos 5 jogos.
    """
    df = df.copy()
    
    # Criando dicionários para acompanhar o histórico dos times
    historico_times = {}
    
    medias_gols_feitos_casa = []
    medias_gols_sofridos_casa = []
    
    for index, row in df.iterrows():
        casa = row['time_casa']
        
        # Inicializa o time no histórico se não existir
        if casa not in historico_times:
            historico_times[casa] = {'feitos': [], 'sofridos': []}
            
        # Calcula a média dos últimos 5 jogos (se houver histórico)
        feitos_ultimos_5 = historico_times[casa]['feitos'][-5:]
        sofridos_ultimos_5 = historico_times[casa]['sofridos'][-5:]
        
        media_f = sum(feitos_ultimos_5)/len(feitos_ultimos_5) if feitos_ultimos_5 else 0
        media_s = sum(sofridos_ultimos_5)/len(sofridos_ultimos_5) if sofridos_ultimos_5 else 0
        
        medias_gols_feitos_casa.append(media_f)
        medias_gols_sofridos_casa.append(media_s)
        
        # Atualiza o histórico para o PRÓXIMO jogo
        historico_times[casa]['feitos'].append(row['gols_casa'])
        historico_times[casa]['sofridos'].append(row['gols_fora'])
        
    df['media_gols_feitos_casa_5j'] = medias_gols_feitos_casa
    df['media_gols_sofridos_casa_5j'] = medias_gols_sofridos_casa
    
    # Remove as primeiras rodadas onde não há histórico suficiente
    return df[df['media_gols_feitos_casa_5j'] > 0].reset_index(drop=True)
