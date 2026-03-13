import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd

class BettingExpert:
    def __init__(self, name, features):
        self.name = name
        self.features = features
        self.model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, eval_metric='logloss')

    def treinar(self, df, target):
        X = df[self.features]
        y = df[target]
        
        # Split para validação
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.model.fit(X_train, y_train)
        
        preds = self.model.predict(X_test)
        probas = self.model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, preds)
        
        return acc, probas, y_test

def treinar_cerebro(df, nome, features, target, col_odd):
    """
    Função de conveniência para o pipeline principal.
    Retorna o modelo, X_test, Odds, Probabilidades e o DataFrame original correspondente.
    """
    expert = BettingExpert(nome, features)
    
    X = df[features]
    y = df[target]
    
    # Treinamos com tudo para prever o próximo (ou usamos split para simular)
    # Para o bot, vamos retornar a previsão do jogo mais recente (última linha)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    expert.model.fit(X_train, y_train)
    
    probas = expert.model.predict_proba(X_test)[:, 1]
    
    # Retornamos os dados do conjunto de teste para o bot exibir
    df_test = df.iloc[X_test.index]
    odds_test = df_test[col_odd]
    
    return expert.model, X_test, odds_test, probas, df_test

def inicializar_especialistas():
    """
    Cria os 3 cérebros especializados (Legado V2).
    """
    experto_resultado = BettingExpert("Resultado Final", ['xg_diff', 'posse_ataque'])
    experto_tatico = BettingExpert("Tático (Remates)", ['remates_p90', 'concessao_adv'])
    experto_disciplinar = BettingExpert("Disciplinar (Cartões)", ['media_arbitro', 'tensao'])
    
    return experto_resultado, experto_tatico, experto_disciplinar
