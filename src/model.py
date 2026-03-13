import xgboost as xgb
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def calcular_roi(y_true, odds, prob_prevista, margem_seguranca=0.03):
    """Calcula o +EV garantindo que a aposta só ocorra se a odd da casa for desajustada."""
    prob_implicita = 1 / odds
    
    # REGRA DE OURO +EV: Probabilidade da IA > Probabilidade da Casa
    apostar_mask = prob_prevista > (prob_implicita + margem_seguranca)
    
    apostas_feitas = y_true[apostar_mask]
    odds_apostadas = odds[apostar_mask]
    
    unidades_investidas = len(apostas_feitas)
    retorno = np.where(apostas_feitas == 1, odds_apostadas - 1, -1)
    lucro = retorno.sum()
    roi = (lucro / unidades_investidas) * 100 if unidades_investidas > 0 else 0
    
    return unidades_investidas, lucro, roi, apostar_mask

def treinar_cerebro(df_treino, df_futuro, nome_mercado, features, target, col_odd):
    """Treina com o passado (FT) e prevê o futuro (NS)."""
    print(f"\nTreinando Cérebro: {nome_mercado}...")
    
    # Validação de classes no treino
    if df_treino[target].nunique() < 2:
        print(f"⚠️ Aviso [{nome_mercado}]: Dados de treino sem variação. Pulando...")
        return None, pd.DataFrame(), pd.Series(), pd.Series(), pd.DataFrame()

    # 1. Treino (Passado)
    X_train = df_treino[features]
    y_train = df_treino[target]
    
    modelo = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=3, eval_metric='logloss')
    modelo.fit(X_train, y_train)
    
    # 2. Previsão (Futuro) - Se não houver jogos futuros, retorna vazio
    if df_futuro.empty:
        return modelo, pd.DataFrame(), pd.Series(), pd.Series(), pd.DataFrame()

    # Filtrar apenas as colunas necessárias para o X_futuro
    X_futuro = df_futuro[features]
    odds_futuro = df_futuro[col_odd]
    
    prob_prevista = modelo.predict_proba(X_futuro)[:, 1]
    
    # Filtra apenas as apostas de valor no futuro
    prob_implicita = 1 / odds_futuro
    mask_valor = prob_prevista > (prob_implicita + 0.03) # 3% de margem de segurança
    
    return modelo, X_futuro[mask_valor], odds_futuro[mask_valor], prob_prevista[mask_valor], df_futuro[mask_valor]
