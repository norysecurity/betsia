import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class BettingExpert:
    def __init__(self, name, features):
        self.name = name
        self.features = features
        self.model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=4, eval_metric='logloss')

    def treinar(self, df, target):
        X = df[self.features]
        y = df[target]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        self.model.fit(X_train, y_train)
        
        preds = self.model.predict(X_test)
        probas = self.model.predict_proba(X_test)[:, 1]
        acc = accuracy_score(y_test, preds)
        
        return acc, probas, y_test

def inicializar_especialistas():
    """
    Cria os 3 cérebros especializados.
    """
    # 1. Resultado Final (1X2)
    experto_resultado = BettingExpert("Resultado Final", ['media_xg_casa_5j', 'gols_casa'])
    
    # 2. Tático (Remates)
    experto_tatico = BettingExpert("Tático (Remates)", ['remates_total', 'minutos'])
    
    # 3. Disciplinar (Cartões)
    experto_disciplinar = BettingExpert("Disciplinar (Cartões)", ['faltas_cometidas'])
    
    return experto_resultado, experto_tatico, experto_disciplinar
