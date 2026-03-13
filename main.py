import telebot
import pandas as pd
import time
from telebot.apihelper import ApiTelegramException
from src.config import TELEGRAM_TOKEN
from src.api_client import coletar_dados_api
from src.model import treinar_cerebro

# Inicialização com Log
print("🚀 Iniciando Bot Sniper V8...")
try:
    bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")
    VALOR_UNIDADE = 50.00 
    print("✅ Token do Telegram validado!")
except Exception as e:
    print(f"❌ Erro ao inicializar Bot: {e}")
    exit(1)

def safe_send_message(chat_id, text, **kwargs):
    """Envia mensagem tratando o erro 429 (Rate Limit) do Telegram."""
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except ApiTelegramException as e:
        if e.error_code == 429:
            retry_after = int(e.result_json.get('parameters', {}).get('retry_after', 30))
            print(f"⚠️ Rate Limit atingido! Aguardando {retry_after} segundos...")
            time.sleep(retry_after + 1)
            return bot.send_message(chat_id, text, **kwargs)
        else:
            print(f"❌ Erro na API do Telegram: {e}")
            raise e
    except Exception as e:
        print(f"❌ Erro inesperado ao enviar mensagem: {e}")
        raise e

def disparar_alerta_didatico(mercado, jogo_info, odd_minima, odd_atual, prob_ia, acao_direta, explicacao_simples, instrucao_bet365, chat_id):
    prob_casa = (1 / odd_atual) * 100 
    prob_nossa = prob_ia * 100 
    
    # Captura a casa dinamicamente (fallback para Bet365 se houver erro)
    nome_casa = jogo_info.get('casa_de_aposta', 'Bet365')
    
    texto = (
        f"🚨 *ALERTA DE APOSTA: {mercado}* 🚨\n\n"
        f"⚽ *Jogo:* {jogo_info['time_casa']} x {jogo_info['time_fora']}\n\n"
        f"🎯 *O QUE VOCÊ DEVE FAZER AGORA:*\n👉 *{acao_direta}*\n\n"
        f"💡 *Por que apostar nisso?*\n{explicacao_simples}\n\n"
        f"📊 *A Matemática:*\n"
        f"A casa *{nome_casa}* dá *{prob_casa:.1f}%* de chance (Odd {odd_atual:.2f}).\n"
        f"A nossa IA calcula a chance real em *{prob_nossa:.1f}%*!\n"
        f"Temos vantagem matemática contra a casa.\n\n"
        f"💰 *Gestão de Banca:* Aposte R$ {VALOR_UNIDADE:.2f} (1 Unidade)\n"
        f"📱 *Onde Apostar:* {nome_casa} -> {instrucao_bet365}"
    )
    safe_send_message(chat_id, texto)

@bot.message_handler(commands=['start'])
def enviar_boas_vindas(message):
    print(f"👤 Comando /start recebido de {message.from_user.first_name}")
    safe_send_message(message.chat.id, "🤖 *Sniper Betting AI V8 (Web Scraper) Ativado!*\n\nAgora busco jogos diretamente em fontes públicas da web, sem limites de API.\n\nDigite /analisar para iniciar a varredura.")

@bot.message_handler(commands=['analisar'])
def executar_analise_telegram(message):
    chat_id = message.chat.id
    print(f"📊 Comando /analisar recebido. Iniciando processamento...")
    bot.reply_to(message, "⏳ *Iniciando Raspagem Web e Análise Matemática...*")
    
    total_alertas_global = 0

    try:
        df = coletar_dados_api()
        if df is None or df.empty:
            print("⚠️ Scraper retornou DataFrame vazio.")
            safe_send_message(chat_id, "📉 Nenhum dado coletado pelo scraper no momento.")
            return

        print(f"✅ Dados coletados: {len(df)} partidas.")

        # Separação: Passado vs Futuro
        df_treino = df[df['status'] == 'FT'].copy()
        df_futuro = df[df['status'] == 'NS'].copy()

        print(f"📈 Treino: {len(df_treino)} | Previsão: {len(df_futuro)}")

        if df_futuro.empty:
            safe_send_message(chat_id, "📉 Não há jogos futuros agendados para análise no momento.")
            return

        # Execução dos Especialistas
        print("🧠 Treinando Especialistas de IA...")
        res1 = treinar_cerebro(df_treino, df_futuro, "RESULTADO", ['xg_diff', 'posse_ataque'], 'resultado_casa', 'odd_casa')
        res2 = treinar_cerebro(df_treino, df_futuro, "REMATES", ['remates_p90', 'concessao_adv'], 'remates_over_2_5', 'odd_remates_over_2_5')
        res3 = treinar_cerebro(df_treino, df_futuro, "CARTÕES", ['media_arbitro', 'tensao'], 'cartoes_over_4_5', 'odd_cartoes_over_4_5')

        # Processar resultados do Cérebro 1
        if not res1[4].empty:
            print(f"🎯 Alertas VITÓRIA: {len(res1[4])}")
            for i in range(len(res1[4])):
                disparar_alerta_didatico("VITÓRIA", res1[4].iloc[i], 0, res1[2].iloc[i], res1[3][i], 
                    f"Vitória do {res1[4].iloc[i]['time_casa']}", "Padrão estatístico favorável ao mandante.", 
                    "Aba 'Resultado Final'", chat_id)
                total_alertas_global += 1
                time.sleep(0.5) # Anti-spam preventivo

        # Processar resultados do Cérebro 2
        if not res2[4].empty:
            print(f"🎯 Alertas CHUTES: {len(res2[4])}")
            for i in range(len(res2[4])):
                disparar_alerta_didatico("CHUTES", res2[4].iloc[i], 0, res2[2].iloc[i], res2[3][i], 
                    "Mais de 2.5 Chutes", "Alta probabilidade de jogo aberto.", 
                    "Aba 'Estatísticas de Jogador'", chat_id)
                total_alertas_global += 1
                time.sleep(0.5) # Anti-spam preventivo

        # Processar resultados do Cérebro 3
        if not res3[4].empty:
            print(f"🎯 Alertas CARTÕES: {len(res3[4])}")
            for i in range(len(res3[4])):
                disparar_alerta_didatico("CARTÕES", res3[4].iloc[i], 0, res3[2].iloc[i], res3[3][i], 
                    "Mais de 4.5 Cartões", "Jogo tenso com árbitro rigoroso.", 
                    "Aba 'Cartões'", chat_id)
                total_alertas_global += 1
                time.sleep(0.5) # Anti-spam preventivo

    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        try:
            safe_send_message(chat_id, f"❌ Erro na execução: {str(e)}")
        except:
            pass

    if total_alertas_global == 0:
        safe_send_message(chat_id, "📉 Varredura concluída. Nenhuma oportunidade +EV encontrada hoje.")
    else:
        print(f"🏁 Análise finalizada. {total_alertas_global} alertas enviados.")
        safe_send_message(chat_id, f"✅ *ANÁLISE CONCLUÍDA!*\n\nEncontrei {total_alertas_global} oportunidades lucrativas.")

if __name__ == "__main__":
    print("🤖 Bot rodando. Acesse o Telegram e digite /analisar")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Erro no polling: {e}. Reiniciando em 5 segundos...")
            time.sleep(5)
