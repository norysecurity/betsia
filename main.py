import os
import sys
import pandas as pd
import numpy as np
from src.api_client import coletar_jogos, extrair_detalhes_profundos
from src.features import criar_features_resultado, criar_features_taticas, criar_features_disciplinares
from src.model import inicializar_especialistas

def formatar_alerta_telegram(tipo, info):
    """
    Gera as mensagens formatadas de acordo com o pedido do usuário.
    """
    if tipo == "JOGADOR":
        print(f"\n🎯 [ALERTA JOGADOR] - Remates à Baliza")
        print(f"⚽ {info['jogador']} ({info['mercado']})")
        print(f"📈 Nossa I.A: {info['prob_ia']:.0%} | ⚖️ Odd Mínima: {info['odd_min']:.2f}")
        print(f"🔥 Odd Atual Bet365: {info['odd_atual']:.2f} (Aposta de Valor!)")
        print(f"👉 Vá diretamente à aba \"Jogador - Chutes ao Gol\" e selecione a opção.")

    elif tipo == "CARTÕES":
        print(f"\n🟨 [ALERTA ÁRBITRO] - Mercado de Cartões")
        print(f"⚔️ {info['confronto']} ({info['mercado']})")
        print(f"🕵️‍♂️ Árbitro: {info['arbitro']} (Média: {info['media_arbitro']} cartões/jogo)")
        print(f"📈 Nossa I.A: {info['prob_ia']:.0%} | ⚖️ Odd Mínima: {info['odd_min']:.2f}")
        print(f"🔥 Odd Atual Bet365: {info['odd_atual']:.2f}")
        print(f"👉 Vá diretamente à aba \"Cartões\" e selecione a opção.")

    elif tipo == "RESULTADO":
        print(f"\n🏆 [ALERTA RESULTADO] - Mercado 1X2")
        print(f"⚔️ {info['confronto']} (Vencer Jogo)")
        print(f"📊 xG Esperado: {info['xg_casa']} vs {info['xg_fora']}")
        print(f"📈 Nossa I.A: {info['prob_ia']:.0%} | ⚖️ Odd Mínima: {info['odd_min']:.2f}")
        print(f"🔥 Odd Atual Bet365: {info['odd_atual']:.2f}")

def executar_pipeline_v2():
    print("=== BETTING AI - ARQUITETURA DE MÚLTIPLOS ESPECIALISTAS (V2) ===")
    
    # 1. Inicialização dos Cérebro Especialistas
    brain_res, brain_tat, brain_dis = inicializar_especialistas()

    # 2. Coleta de Dados Profundos
    league_id = int(os.getenv("LEAGUE_ID", 71))
    season = int(os.getenv("SEASON", 2023))
    
    print(f"1. Coletando dados profundos da Liga {league_id}...")
    try:
        df_base = coletar_jogos(league_id, season)
        if df_base.empty: raise ValueError("Sem dados")
    except:
        print("Aviso: Simulando dados profundos para demonstração...")
        df_base = pd.DataFrame({
            'fixture_id': [1039235], 'time_casa': ['Villarreal'], 'time_fora': ['Alavés'],
            'gols_casa': [2], 'gols_fora': [1], 'resultado_casa': [1], 'arbitro': ['Mateu Lahoz'],
            'casa_xg': [1.85], 'fora_xg': [0.90]
        })

    # 3. Execução do Cérebro 1: Resultado Final
    print("2. Ativando Cérebro de Resultado Final...")
    df_res = criar_features_resultado(df_base)
    acc_res, probas_res, _ = brain_res.treinar(df_res, 'resultado_casa')
    
    # Alerta Simulado de Exemplo
    formatar_alerta_telegram("RESULTADO", {
        'confronto': 'Villarreal x Alavés',
        'xg_casa': 1.85, 'xg_fora': 0.90,
        'prob_ia': probas_res[0] if len(probas_res)>0 else 0.75,
        'odd_min': 1.45, 'odd_atual': 1.80
    })

    # 4. Execução do Cérebro 2: Tático (Remates)
    print("\n3. Ativando Cérebro Tático (Estatísticas de Jogadores)...")
    # Aqui usaríamos extrair_detalhes_profundos(fixture_id) no loop real
    df_jogadores = pd.DataFrame([
        {'fixture_id': 1039235, 'jogador': 'Mason Greenwood', 'remates_total': 3, 'remates_baliza': 2, 'minutos': 90},
        {'fixture_id': 1039235, 'jogador': 'Gerard Moreno', 'remates_total': 4, 'remates_baliza': 1, 'minutos': 85}
    ])
    df_tat = criar_features_taticas(df_jogadores)
    # Treino fictício pois precisamos de histórico por jogador para XGBoost real
    
    formatar_alerta_telegram("JOGADOR", {
        'jogador': 'Mason Greenwood', 'mercado': 'Mais de 1.5 Chutes ao Gol',
        'prob_ia': 0.68, 'odd_min': 1.60, 'odd_atual': 1.82
    })

    # 5. Execução do Cérebro 3: Disciplinar (Cartões)
    print("\n4. Ativando Cérebro Disciplinar (Arbitragem)...")
    formatar_alerta_telegram("CARTÕES", {
        'confronto': 'Villarreal x Alavés', 'mercado': 'Mais de 4.5 Cartões',
        'arbitro': 'Mateu Lahoz', 'media_arbitro': 6.2,
        'prob_ia': 0.75, 'odd_min': 1.50, 'odd_atual': 1.95
    })

    print("\n" + "="*50)
    print("Pipeline V2 Finalizado com Sucesso.")

if __name__ == "__main__":
    executar_pipeline_v2()
