import os
import sys
import pandas as pd
import numpy as np
from src.api_client import coletar_jogos
from src.features import criar_features
from src.model import treinar_modelo

def executar_pipeline():
    print("=== INICIANDO PIPELINE DE BETTING AI ===")
    
    # 1. Coleta ou Simulação de Dados
    league_id = int(os.getenv("LEAGUE_ID", 71))
    season = int(os.getenv("SEASON", 2023))
    
    print(f"1. Coletando dados da Liga {league_id}, Temporada {season}...")
    try:
        df_bruto = coletar_jogos(league_id, season)
        if df_bruto.empty:
            raise ValueError("API não retornou dados.")
        print(f"Sucesso! {len(df_bruto)} partidas coletadas.")
    except Exception as e:
        print(f"Aviso: Erro na API ({e}). Usando dados simulados para demonstração.")
        # Simulação mínima para o código rodar caso o usuário não tenha a chave ainda
        df_bruto = pd.DataFrame({
            'time_casa': ['Time A', 'Time B']*100,
            'time_fora': ['Time C', 'Time D']*100,
            'gols_casa': np.random.randint(0, 4, 200),
            'gols_fora': np.random.randint(0, 4, 200),
            'resultado_casa': np.random.randint(0, 2, 200),
            'data': pd.date_range(start='2023-01-01', periods=200)
        })

    # 2. Feature Engineering
    print("2. Gerando estatísticas avançadas (Feature Engineering)...")
    df_processado = criar_features(df_bruto)
    print(f"Partidas processadas com histórico: {len(df_processado)}")

    # 3. Modelagem e Backtest
    print("3. Treinando o modelo XGBoost...")
    modelo, acuracia, probas, y_test = treinar_modelo(df_processado)
    print(f"Treinamento concluído. Acurácia Técnica: {acuracia:.2%}")

    # 4. Lógica de Value Betting (+EV)
    print("\n--- RELATÓRIO DE VALUE BETTING (+EV) ---")
    # Simulando odds da casa (1 / Probabilidade Real + margem)
    odds_casa = 1 / (probas + 0.05) 
    prob_implicita = 1 / odds_casa
    
    margem_seguranca = 0.02
    apostar_mask = probas > (prob_implicita + margem_seguranca)
    
    apostas_feitas = y_test[apostar_mask]
    odds_vencidas = odds_casa[apostar_mask]
    
    total_apostas = len(apostas_feitas)
    lucro = np.where(apostas_feitas == 1, odds_vencidas - 1, -1).sum()
    roi = (lucro / total_apostas) * 100 if total_apostas > 0 else 0
    
    print(f"Total de Value Bets encontradas: {total_apostas}")
    print(f"Lucro Estimado: {lucro:.2f} unidades")
    print(f"ROI: {roi:.2f}%")
    print("=========================================")

if __name__ == "__main__":
    executar_pipeline()
