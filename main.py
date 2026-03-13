import telebot
import pandas as pd
from src.config import TELEGRAM_TOKEN
from src.api_client import coletar_dados_api
from src.model import treinar_cerebro

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")
VALOR_UNIDADE = 50.00 

def disparar_alerta_didatico(mercado, jogo_info, odd_minima, odd_atual, prob_ia, acao_direta, explicacao_simples, instrucao_bet365, chat_id):
    prob_casa = (1 / odd_atual) * 100 
    prob_nossa = prob_ia * 100 
    
    texto = (
        f"🚨 *ALERTA DE APOSTA: {mercado}* 🚨\n\n"
        f"⚽ *Jogo:* {jogo_info['time_casa']} x {jogo_info['time_fora']}\n\n"
        f"🎯 *O QUE VOCÊ DEVE FAZER AGORA:*\n👉 *{acao_direta}*\n\n"
        f"💡 *Por que apostar nisso?*\n{explicacao_simples}\n\n"
        f"📊 *A Matemática:*\n"
        f"A Bet365 dá *{prob_casa:.1f}%* de chance (Odd {odd_atual:.2f}).\n"
        f"A nossa IA calcula a chance real em *{prob_nossa:.1f}%*!\n"
        f"Temos vantagem matemática contra a casa.\n\n"
        f"💰 *Gestão de Banca:* Aposte R$ {VALOR_UNIDADE:.2f} (1 Unidade)\n"
        f"📱 *Na Bet365:* {instrucao_bet365}"
    )
    bot.send_message(chat_id, texto)

@bot.message_handler(commands=['start'])
def enviar_boas_vindas(message):
    bot.reply_to(message, "🤖 *Sniper Bet365 Ativado!*\n\nAnaliso os jogos que VÃO ACONTECER hoje e amanhã. Digite /analisar para iniciar.")

@bot.message_handler(commands=['analisar'])
def executar_analise_telegram(message):
    chat_id = message.chat.id
    bot.reply_to(message, "⏳ *Analisando o mercado futuro...* Buscando falhas na Bet365.")
    
    try:
        df = coletar_dados_api()
        if df.empty:
            bot.send_message(chat_id, "❌ Erro ao baixar dados.")
            return

        # Separação crucial: Treino (Passado) vs Previsão (Futuro)
        df_treino = df[df['status'] == 'FT'].copy()
        df_futuro = df[df['status'] == 'NS'].copy()

        if df_futuro.empty:
             bot.send_message(chat_id, "📉 Não há jogos futuros agendados para análise no momento.")
             return

        # Execução dos 3 Cérebros
        mod1, x1, odd1, prob1, prev1 = treinar_cerebro(df_treino, df_futuro, "RESULTADO FINAL", ['xg_diff', 'posse_ataque'], 'resultado_casa', 'odd_casa')
        mod2, x2, odd2, prob2, prev2 = treinar_cerebro(df_treino, df_futuro, "REMATES JOGADOR", ['remates_p90', 'concessao_adv'], 'remates_over_2_5', 'odd_remates_over_2_5')
        mod3, x3, odd3, prob3, prev3 = treinar_cerebro(df_treino, df_futuro, "CARTÕES", ['media_arbitro', 'tensao'], 'cartoes_over_4_5', 'odd_cartoes_over_4_5')

        alertas = 0
        if not prev1.empty:
            for i in range(len(prev1)):
                jogo = prev1.iloc[i]
                disparar_alerta_didatico("VITÓRIA DO MANDANTE", jogo, 1/prob1[i], odd1.iloc[i], prob1[i], 
                    f"APOSTE NA VITÓRIA DO {jogo['time_casa'].upper()}", 
                    f"O time do {jogo['time_casa']} domina as métricas ofensivas neste confronto.", 
                    "Aba 'Resultado Final' -> Time da Casa", chat_id)
                alertas += 1
            
        if not prev2.empty:
            for i in range(len(prev2)):
                jogo = prev2.iloc[i]
                disparar_alerta_didatico("CHUTES AO GOL", jogo, 1/prob2[i], odd2.iloc[i], prob2[i], 
                    "APOSTE EM MAIS DE 2.5 CHUTES DO ATACANTE", 
                    f"A defesa do {jogo['time_fora']} permite muitas finalizações de fora da área.", 
                    "Aba 'Jogador - Chutes ao Golo' -> Mais de 2.5", chat_id)
                alertas += 1

        if not prev3.empty:
            for i in range(len(prev3)):
                jogo = prev3.iloc[i]
                disparar_alerta_didatico("TOTAL DE CARTÕES", jogo, 1/prob3[i], odd3.iloc[i], prob3[i], 
                    "APOSTE EM MAIS DE 4.5 CARTÕES", 
                    "Árbitro rigoroso apitando um jogo com alto índice de tensão.", 
                    "Aba 'Cartões' -> Partida/Mais de 4.5", chat_id)
                alertas += 1

        if alertas == 0:
            bot.send_message(chat_id, "📉 O mercado está justo. Nenhuma Aposta de Valor (+EV) encontrada nos jogos futuros. Dinheiro protegido.")
        else:
            bot.send_message(chat_id, f"✅ Análise concluída! Te mandei {alertas} ordens de apostas.")

    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro: {e}")

if __name__ == "__main__":
    print("🤖 Bot rodando. Acesse o Telegram e digite /analisar")
    bot.infinity_polling()
