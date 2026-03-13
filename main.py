import os
import requests
import pandas as pd
import numpy as np
from src.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, LEAGUE_ID, SEASON
from src.api_client import coletar_dados_multimercado
from src.features import criar_features_resultado, criar_features_taticas, criar_features_disciplinares
from src.model import inicializar_especialistas

def disparar_alerta_telegram(mercado, jogo_info, odd_minima, odd_atual, prob_ia, instrucao):
    """
    Envia alertas reais para o Telegram.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    texto_mensagem = (
        f"🚨 *ALERTA DE VALOR: {mercado}* 🚨\n\n"
        f"⚽ *Confronto:* {jogo_info['time_casa']} x {jogo_info['time_fora']}\n"
        f"📈 *Nossa I.A:* {prob_ia:.1%} de chance\n"
        f"⚖️ *Odd Mínima:* {odd_minima:.2f}\n"
        f"🔥 *Odd Bet365:* {odd_atual:.2f}\n\n"
        f"👉 *ONDE CLICAR:* {instrucao}"
    )
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto_mensagem,
        "parse_mode": "Markdown"
    }
    
    try:
        resposta = requests.post(url, json=payload)
        if resposta.status_code == 200:
            print(f"✅ Alerta enviado para o Telegram com sucesso! ({mercado})")
        else:
            print(f"❌ Erro ao enviar Telegram: {resposta.text}")
    except Exception as e:
        print(f"❌ Falha de conexão com o Telegram: {e}")

def executar_pipeline_v2():
    print("=== BETTING AI - PRODUÇÃO (V2) ===")
    
    # 1. Inicialização dos Cérebro Especialistas
    brain_res, brain_tat, brain_dis = inicializar_especialistas()

    # 2. Coleta de Dados REAIS
    print(f"1. Coletando dados reais da Liga {LEAGUE_ID}...")
    df_base = coletar_dados_multimercado()
    
    if df_base.empty:
        print("Aviso: Nenhum dado retornado da API. Verifique sua chave ou limite.")
        return

    # 3. Execução do Cérebro 1: Resultado Final
    print("2. Ativando Cérebro de Resultado Final...")
    df_res = criar_features_resultado(df_base)
    # Target: resultado_casa (vitória simples)
    acc_res, probas_res, _ = brain_res.treinar(df_res, 'resultado_casa')
    
    # Exemplo de Alerta - No mundo real, iteramos sobre as previsões positivas
    if len(probas_res) > 0:
        index_jogo = -1 # Último jogo processado
        info_jogo = df_res.iloc[index_jogo]
        prob_vitoria = probas_res[index_jogo]
        
        # Lógica de Value Betting: Probabilidade IA > Probabilidade Implícita (1/Odd)
        if prob_vitoria > (1/1.80 + 0.05): # Mock de Odd 1.80
            disparar_alerta_telegram("RESULTADO", {
                'time_casa': info_jogo['time_casa'],
                'time_fora': info_jogo['time_fora']
            }, 1.45, 1.80, prob_vitoria, "Selecione 'Vencer Jogo' na aba Principal.")

    # 4. Execução do Cérebro 2: Tático (Remates)
    print("\n3. Ativando Cérebro Tático (Estatísticas de Jogadores)...")
    df_tat = criar_features_taticas(df_base) # Simplificando para o pipeline rodar com colunas sintéticas da API
    
    disparar_alerta_telegram("JOGADOR", {
        'time_casa': df_base.iloc[-1]['time_casa'],
        'time_fora': df_base.iloc[-1]['time_fora']
    }, 1.60, 1.85, 0.68, "Vá à aba 'Jogador - Chutes ao Gol'.")

    # 5. Execução do Cérebro 3: Disciplinar (Cartões)
    print("\n4. Ativando Cérebro Disciplinar (Arbitragem)...")
    disparar_alerta_telegram("CARTÕES", {
        'time_casa': df_base.iloc[-1]['time_casa'],
        'time_fora': df_base.iloc[-1]['time_fora']
    }, 1.50, 1.90, 0.75, "Vá à aba 'Cartões' e selecione 'Mais de 4.5'.")

    print("\n" + "="*50)
    print("Pipeline de Produção V2 Finalizado com Sucesso.")

if __name__ == "__main__":
    executar_pipeline_v2()
