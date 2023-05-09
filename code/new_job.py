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


def start_newjob(update: Update, context: CallbackContext) -> int:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    if 'command' in context.user_data:
        update.message.reply_text('[' + context.user_data['command'] + ']: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['multipleCommandWarning'], quote=False)
        return main.ConversationHandler.END
    context.user_data['command'] = '/newjob'
    print('/newjob triggered by', user)
    context.user_data['current_conversation_message'] = [update.message, update.message.reply_text('[/newjob]: @' + user + ' 呢條係咩片?\n請以"YYMMDD 片名"格式輸入\n/cancel 取消command', quote=True)]
    return db.GET_RESPONSE