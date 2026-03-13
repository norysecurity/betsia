import telebot
from src.config import TELEGRAM_TOKEN
from src.api_client import coletar_dados_multimercado
from src.model import treinar_cerebro

# Inicializa o Bot do Telegram
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")

def disparar_alerta(mercado, jogo_info, odd_minima, odd_atual, prob_ia, instrucao, chat_id):
    """Envia o alerta formatado como resposta ao comando."""
    texto = (
        f"🚨 *ALERTA DE VALOR: {mercado}* 🚨\n\n"
        f"⚽ *Confronto:* {jogo_info['time_casa']} x {jogo_info['time_fora']}\n"
        f"📈 *Nossa I.A:* {prob_ia:.1%} de chance\n"
        f"⚖️ *Odd Mínima:* {odd_minima:.2f}\n"
        f"🔥 *Odd Bet365:* {odd_atual:.2f}\n\n"
        f"👉 *ONDE CLICAR:* {instrucao}"
    )
    bot.send_message(chat_id, texto)

@bot.message_handler(commands=['start'])
def enviar_boas_vindas(message):
    bot.reply_to(message, "🤖 *Sniper Bet365 Ativado!*\n\nSou sua Inteligência Artificial de Value Betting (+EV). Digite /analisar a qualquer momento para eu varrer o mercado.")

@bot.message_handler(commands=['analisar'])
def executar_analise_telegram(message):
    chat_id = message.chat.id
    bot.reply_to(message, "⏳ *Iniciando varredura multimercado na API-Football...* Aguarde enquanto os 3 cérebros calculam as probabilidades.")
    
    try:
        # 1. Coleta de dados reais (respeitando o limite grátis)
        df = coletar_dados_multimercado()
        
        if df.empty:
            bot.send_message(chat_id, "❌ *Erro:* Nenhum dado retornado. Verifique se você ativou sua chave na API-Sports.")
            return

        # 2. Executa os Cérebros (usando dados reais e as features disponíveis)
        # Cérebro 1: Resultado Final
        mod_1, x1, odd1, prob1, df_orig1 = treinar_cerebro(
            df, "RESULTADO FINAL (1X2)", 
            ['xg_diff', 'posse_ataque'], 'resultado_casa', 'odd_casa'
        )
        
        # Cérebro 2: Remates
        mod_2, x2, odd2, prob2, df_orig2 = treinar_cerebro(
            df, "REMATES JOGADOR", 
            ['remates_p90', 'concessao_adv'], 'remates_over_2_5', 'odd_remates_over_2_5'
        )
        
        # Cérebro 3: Cartões
        mod_3, x3, odd3, prob3, df_orig3 = treinar_cerebro(
            df, "CARTÕES (+4.5)", 
            ['media_arbitro', 'tensao'], 'cartoes_over_4_5', 'odd_cartoes_over_4_5'
        )

        # 3. Dispara os Alertas encontrados
        alertas_encontrados = 0
        
        if not df_orig1.empty:
            disparar_alerta("Vitória Mandante", df_orig1.iloc[0], 1/prob1[0], odd1.iloc[0], prob1[0], "Resultado Final -> Time da Casa", chat_id)
            alertas_encontrados += 1
            
        if not df_orig2.empty:
            disparar_alerta("+2.5 Chutes ao Gol", df_orig2.iloc[0], 1/prob2[0], odd2.iloc[0], prob2[0], "Jogador - Chutes ao Gol -> Mais de 2.5", chat_id)
            alertas_encontrados += 1

        if not df_orig3.empty:
            disparar_alerta("Mais de 4.5 Cartões", df_orig3.iloc[0], 1/prob3[0], odd3.iloc[0], prob3[0], "Cartões -> Mais de 4.5", chat_id)
            alertas_encontrados += 1

        if alertas_encontrados == 0:
            bot.send_message(chat_id, "📉 Análise concluída. O mercado está bem precificado agora. Nenhuma Aposta de Valor (+EV) encontrada nesta varredura. Tente novamente mais tarde!")
        else:
            bot.send_message(chat_id, f"✅ Análise concluída! Foram encontrados *{alertas_encontrados} alertas* de valor.")

    except Exception as e:
        bot.send_message(chat_id, f"❌ *Erro na execução:* {e}")

if __name__ == "__main__":
    print("🤖 Bot Telegram rodando em modo interativo (Polling)... Pressione Ctrl+C para parar.")
    # Mantém o bot escutando infinitamente
    bot.infinity_polling()
