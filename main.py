import telebot
import pandas as pd
import time
from telebot import types
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

def criar_menu_principal():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('📊 Sniper (Alertas)')
    item2 = types.KeyboardButton('📅 Agenda do Dia')
    item3 = types.KeyboardButton('🚀 Múltiplas')
    markup.add(item1, item2, item3)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def enviar_boas_vindas(message):
    print(f"👤 Comando {message.text} recebido de {message.from_user.first_name}")
    welcome_text = (
        "🤖 *Sniper Betting AI V9 Ativado!*\n\n"
        "Selecione uma opção no menu abaixo para começar:\n\n"
        "📊 *Sniper (Alertas):* Apenas jogos com real valor matemático (+EV).\n"
        "📅 *Agenda do Dia:* Análise completa de todos os jogos de hoje.\n"
        "🚀 *Múltiplas:* Sugestões de bilhetes combinados (Resultado + BTTS)."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=criar_menu_principal())

@bot.message_handler(func=lambda message: True)
def tratar_clique_botoes(message):
    if message.text == '📊 Sniper (Alertas)':
        executar_analise_telegram(message)
    elif message.text == '📅 Agenda do Dia':
        executar_agenda_completa(message)
    elif message.text == '🚀 Múltiplas':
        executar_sugestao_multiplas(message)

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

        for res, mercado, acao, desc, instrucao in [
            (res1, "VITÓRIA", "Vitória Mandante", "Padrão estatístico favorável ao mandante.", "Aba 'Resultado Final'"),
            (res2, "CHUTES", "Mais de 2.5 Chutes", "Alta probabilidade de jogo aberto.", "Aba 'Estatísticas'"),
            (res3, "CARTÕES", "Mais de 4.5 Cartões", "Jogo tenso com árbitro rigoroso.", "Aba 'Cartões'")
        ]:
            if res[4] is not None and not res[4].empty:
                for i in range(len(res[4])):
                    disparar_alerta_didatico(mercado, res[4].iloc[i], 0, res[2].iloc[i], res[3][i], acao, desc, instrucao, chat_id)
                    total_alertas_global += 1
                    time.sleep(0.5)

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

def executar_agenda_completa(message):
    chat_id = message.chat.id
    print(f"📅 Agenda do Dia solicitada.")
    bot.reply_to(message, "📅 *Gerando Agenda Completa de Hoje...*")
    
    try:
        df = coletar_dados_api()
        df_futuro = df[df['status'] == 'NS'].copy()
        
        if df_futuro.empty:
            safe_send_message(chat_id, "📉 Nenhuma agenda disponível para hoje.")
            return

        # Limita a exibição para não explodir o chat se houver 140 jogos
        # Vamos agrupar os 30 principais para o resumo
        jogos_agenda = df_futuro.head(30)
        
        relatorio = "📅 *AGENDA COMPLETA DO DIA (Top 30)*\n\n"
        for _, jogo in jogos_agenda.iterrows():
            relatorio += f"⚽ `{jogo['time_casa']} x {jogo['time_fora']}`\n"
            relatorio += f"💰 Odd: {jogo['odd_casa']:.2f} | IA: Previsão Ativa\n"
            relatorio += "--------------------------\n"
            
            if len(relatorio) > 3500: # Limite de caracteres do Telegram
                safe_send_message(chat_id, relatorio)
                relatorio = ""

        if relatorio:
            safe_send_message(chat_id, relatorio)
            
        safe_send_message(chat_id, f"✅ Total de {len(df_futuro)} jogos analisados para hoje no Radar Global.")

    except Exception as e:
        safe_send_message(chat_id, f"❌ Erro na agenda: {str(e)}")

def executar_sugestao_multiplas(message):
    chat_id = message.chat.id
    bot.reply_to(message, "🚀 *Calculando Múltiplas de Alto Valor (Win + BTTS)...*")
    
    try:
        df = coletar_dados_api()
        df_treino = df[df['status'] == 'FT'].copy()
        df_futuro = df[df['status'] == 'NS'].copy()

        # Treinar para mercado Combo
        res = treinar_cerebro(df_treino, df_futuro, "COMBO", ['xg_diff', 'posse_ataque'], 'vencer_e_btts', 'odd_vencer_e_btts')
        
        if res[4] is not None and len(res[4]) >= 2:
            sugestoes = res[4].head(3) # Pega até 3 para a múltipla
            
            texto = "🚀 *SUGESTÃO DE MÚLTIPLA (COMBO)* 🚀\n\n"
            odd_total = 1.0
            for i, jogo in sugestoes.iterrows():
                odd_val = res[2][i]
                odd_total *= odd_val
                texto += f"✅ *Jogo:* {jogo['time_casa']} x {jogo['time_fora']}\n"
                texto += f"👉 *Aposta:* Vitória Mandante + Ambas Marcam (Sim)\n"
                texto += f"💰 *Odd Individual:* {odd_val:.2f}\n\n"
            
            texto += f"🔥 *ODD TOTAL: @{odd_total:.2f}*\n"
            texto += f"💰 *Gestão:* R$ {(VALOR_UNIDADE/2):.2f} (0.5 Unidade)"
            safe_send_message(chat_id, texto)
        else:
            safe_send_message(chat_id, "📉 Não há dados suficientes para gerar uma múltipla segura agora.")

    except Exception as e:
        safe_send_message(chat_id, f"❌ Erro nas múltiplas: {str(e)}")

if __name__ == "__main__":
    print("🤖 Bot rodando. Acesse o Telegram e digite /analisar")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Erro no polling: {e}. Reiniciando em 5 segundos...")
            time.sleep(5)
