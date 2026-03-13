import telebot
import pandas as pd
import time
import schedule
import threading
import os
from telebot import types
from telebot.apihelper import ApiTelegramException
from src.config import TELEGRAM_TOKEN
from src.api_client import coletar_dados_api
from src.model import treinar_cerebro
from db_manager import DBManager
from pdf_generator import gerar_relatorio_pdf

# Configurações
TELEGRAM_VIP_GROUP_ID = os.getenv("TELEGRAM_VIP_GROUP_ID", "-100123456789") # ID do Grupo VIP
VALOR_UNIDADE = 50.00
db = DBManager()

# Inicialização
print("🚀 Iniciando Sniper V10 (Arquitetura Premium)...")
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")

# --- UTILITÁRIOS ---

def safe_send_message(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except ApiTelegramException as e:
        if e.error_code == 429:
            retry_after = int(e.result_json.get('parameters', {}).get('retry_after', 30))
            time.sleep(retry_after + 1)
            return bot.send_message(chat_id, text, **kwargs)
        raise e

def criar_menu_inline():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📅 Agenda do Dia (Todos)", callback_data="agenda"))
    markup.row(types.InlineKeyboardButton("🚀 Múltiplas do Dia (1x dia)", callback_data="multiplas"))
    markup.row(types.InlineKeyboardButton("📊 Sniper Semanal (1x semana)", callback_data="sniper_semanal"))
    return markup

# --- LÓGICA DE NEGÓCIO ---

@bot.message_handler(commands=['start', 'menu'])
def cmd_menu(message):
    welcome = (
        "💎 *BETS IA PREMIUM V10*\n\n"
        "Bem-vindo ao seu painel exclusivo de análises.\n"
        "Selecione uma opção abaixo para começar:"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=criar_menu_inline())

@bot.callback_query_handler(func=lambda call: True)
def callback_interface(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    # UX FLUIDA: Remove botões imediatamente
    bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=None)

    # BYPASS ADMIN: Liberação total para o usuário solicitado
    eh_admin = (user_id == 8633174140)

    if call.data == "agenda":
        bot.edit_message_text("⏳ *A preparar a Agenda Detalhada...*", chat_id, msg_id)
        executar_agenda_completa(chat_id)

    elif call.data == "multiplas":
        if not eh_admin:
            permitido, proximo = db.check_quota(user_id, 'daily')
            if not permitido:
                bot.send_message(chat_id, f"⚠️ *Limite Diário Excedido!*\nNovo bilhete disponível em: `{proximo.strftime('%d/%m %H:%M')}`")
                return
        
        bot.edit_message_text("⏳ *A processar Múltiplas +EV...*", chat_id, msg_id)
        processar_multiplas_pdf(chat_id, user_id)

    elif call.data == "sniper_semanal":
        if not eh_admin:
            permitido, proximo = db.check_quota(user_id, 'weekly')
            if not permitido:
                bot.send_message(chat_id, f"⚠️ *Limite Semanal Excedido!*\nSeu próximo relatório Sniper será liberado em: `{proximo.strftime('%d/%m %H:%M')}`")
                return
        
        bot.edit_message_text("⏳ *A gerar Relatório Sniper Completo (PDF)...*", chat_id, msg_id)
        processar_sniper_pdf(chat_id, user_id)

# --- PROCESSADORES ---

def executar_agenda_completa(chat_id):
    df = coletar_dados_api()
    df_futuro = df[df['status'] == 'NS'].head(20) # Top 20 para rapidez
    
    res = "📅 *AGENDA DE HOJE*\n\n"
    for _, j in df_futuro.iterrows():
        res += f"⚽ `{j['time_casa']} x {j['time_fora']}` | Odd: {j['odd_casa']:.2f}\n"
    
    safe_send_message(chat_id, res + "\n✅ Use /menu para novas ações.")

def processar_multiplas_pdf(chat_id, user_id):
    try:
        df = coletar_dados_api()
        res = treinar_cerebro(df[df['status']=='FT'], df[df['status']=='NS'], "COMBO", ['xg_diff', 'posse_ataque'], 'vencer_e_btts', 'odd_vencer_e_btts')
        
        if res[4] is not None and not res[4].empty:
            dados = []
            for i in range(min(3, len(res[4]))):
                jogo = res[4].iloc[i]
                odd_casa = res[2].iloc[i]
                prob_ia = res[3][i] * 100
                prob_casa = (1 / odd_casa) * 100
                edge = prob_ia - prob_casa
                
                dados.append({
                    'time_casa': jogo['time_casa'], 
                    'time_fora': jogo['time_fora'],
                    'mercado': 'Resultado + Ambas Marcam', 
                    'odd': odd_casa, 
                    'prob_ia': prob_ia,
                    'prob_casa': prob_casa,
                    'edge': edge
                })
            
            path = gerar_relatorio_pdf("Múltiplas do Dia", dados, f"multipla_{user_id}.pdf")
            
            with open(path, 'rb') as doc:
                bot.send_document(chat_id, doc, caption="🚀 *Seu Bilhete do Dia está pronto!*")
            db.update_quota(user_id, 'daily')
        else:
            bot.send_message(chat_id, "📉 Nenhuma múltipla de valor encontrada no momento.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro ao gerar PDF: {e}")

def processar_sniper_pdf(chat_id, user_id):
    try:
        df = coletar_dados_api()
        # Pega as top oportunidades de todos mercados
        res1 = treinar_cerebro(df[df['status']=='FT'], df[df['status']=='NS'], "SNIPER", ['xg_diff', 'posse_ataque'], 'resultado_casa', 'odd_casa')
        
        if res1[4] is not None:
            dados = []
            for i in range(min(10, len(res1[4]))):
                jogo = res1[4].iloc[i]
                odd_casa = res1[2].iloc[i]
                prob_ia = res1[3][i] * 100
                prob_casa = (1 / odd_casa) * 100
                edge = prob_ia - prob_casa
                
                dados.append({
                    'time_casa': jogo['time_casa'], 
                    'time_fora': jogo['time_fora'],
                    'mercado': 'Vitoria Final (+EV)', 
                    'odd': odd_casa, 
                    'prob_ia': prob_ia,
                    'prob_casa': prob_casa,
                    'edge': edge
                })
            
            path = gerar_relatorio_pdf("Sniper Semanal", dados, f"sniper_{user_id}.pdf")
            
            with open(path, 'rb') as doc:
                bot.send_document(chat_id, doc, caption="📊 *Relatório Sniper Semanal Completo disponível!*")
            db.update_quota(user_id, 'weekly')
    except Exception as e:
        bot.send_message(chat_id, f"❌ Erro no Sniper: {e}")

# --- AUTOMAÇÃO GRUPO VIP ---

def rotina_vip():
    print("📢 Executando Alerta VIP automático...")
    try:
        df = coletar_dados_api()
        res = treinar_cerebro(df[df['status']=='FT'], df[df['status']=='NS'], "VIP", ['xg_diff', 'posse_ataque'], 'resultado_casa', 'odd_casa')
        
        if res[4] is not None and not res[4].empty:
            top5 = res[4].head(5)
            msg = "🌟 *TOP 5 OPORTUNIDADES VIP - HOJE* 🌟\n\n"
            for i in range(len(top5)):
                msg += f"🔥 `{top5.iloc[i]['time_casa']} x {top5.iloc[i]['time_fora']}`\n"
                msg += f"👉 Vitória Mandante | Odd: {res[2].iloc[i]:.2f}\n"
                msg += "--------------------------\n"
            
            safe_send_message(TELEGRAM_VIP_GROUP_ID, msg)
    except Exception as e:
        print(f"❌ Erro na rotina VIP: {e}")

schedule.every().day.at("10:00").do(rotina_vip)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

# --- MAIN ---

if __name__ == "__main__":
    # Thread para o Schedule
    threading.Thread(target=run_schedule, daemon=True).start()
    
    print("🤖 Bot rodando V10. Aguardando interações...")
    while True:
        try:
            bot.infinity_polling(timeout=60)
        except Exception as e:
            time.sleep(5)
