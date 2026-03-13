import xgboost as xgb
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def treinar_modelo(df):
    """
    Treina um classificador XGBoost para prever vitória do time da casa.
    Também calcula ROI e Value Betting simulado.
    """
    features = ['media_gols_feitos_casa_5j', 'media_gols_sofridos_casa_5j']
    X = df[features]
    y = df['resultado_casa']
    
    # Divisão treino/teste (sem embaralhar para respeitar a ordem cronológica)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    modelo = xgb.XGBClassifier(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=4, 
        eval_metric='logloss'
    )
    modelo.fit(X_train, y_train)
    
    preds = modelo.predict(X_test)
    probas = modelo.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, preds)
    
    return modelo, acc, probas, y_test
