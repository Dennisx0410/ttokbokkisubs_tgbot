# libraries
from datetime import date

# tg libraries
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler
)
from youtube_transcript_api import YouTubeTranscriptApi

# code files
import main
import config
import fileio
import functions as bot_funct
import db


def start_setting(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    print('/setting triggered by', user)

    if 'command' in context.user_data:
        return bot_funct.multipleCommandMessage(update, context)

    # check permission
    if user not in db.authorlist and user not in db.whitelist:
        update.message.reply_text('[/setting]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['unauthAnnounceWarning'], quote=False)
        return

    context.user_data['command'] = '/setting'

    # array of button
    keyboard = [[]]
    keyboard_btn = []
    for mode in db.reply_msg_json:
        description = bot_funct.bot_description(mode)
        keyboard_btn.append(InlineKeyboardButton(description, callback_data=mode + ' ' + user))

    btnPerLine = 3
    btn_start = 0
    btn_end = btnPerLine
    for i in range(len(keyboard_btn) // btnPerLine + 1):
        keyboard.append(keyboard_btn[btn_start:btn_end])
        btn_start += btnPerLine
        btn_end += btnPerLine
    
    keyboard.append([InlineKeyboardButton('Cancel', callback_data='cancel ' + user)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['current_conversation_message'] = [update.message.reply_text('@' + user + ' 請問想隻bot進化成點', reply_markup=reply_markup, quote=True)]
    return db.WAITING_SETTING


def button_setting(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user = query.from_user.username

    if user == query.data.split()[1] and 'command' in context.user_data and context.user_data['command'] == '/setting':
        # set new chat id
        db.bot_mode_response = query.data.split()[0]

        # cancel action
        if db.bot_mode_response == 'cancel':
            bot_funct.button_cancel(update, context, ' /setting 已取消')
            print('/setting 被取消咗')
            context.user_data.clear()
            return main.ConversationHandler.END
        db.bot_mode = db.bot_mode_response
        target = bot_funct.bot_description(db.bot_mode)
        today = date.today()
        db.bot_mode_last_update = today

        bot_funct.button_cancel(update, context, ' Bot已變成 ' + target)
        print(user + ' set bot as ' + target)

        bot_funct.DeleteConversationMessage(context.user_data['current_conversation_message'])
        context.user_data['current_conversation_message'] = []
        update.callback_query.message.chat.id = db.tg_chat_id['itTeamChatId'] # it
        update.callback_query.message.reply_text('@' + user + ' 將bot set咗做' + target, quote=False)
        
        context.user_data.clear()
    return main.ConversationHandler.END
