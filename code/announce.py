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


def start_announce(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    print('/announce triggered by', user)

    if 'command' in context.user_data:
        update.message.reply_text('[' + context.user_data['command'] + ']: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['multipleCommandWarning'], quote=False)
        return

    # check permission
    if user not in db.authorlist and user not in db.whitelist:
        update.message.reply_text('[/announce]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['unauthAnnounceWarning'], quote=True)
        return

    msg = update.message.text.split(' ', 1)

    # remove the command and only stores the text
    if len(msg) <= 1:
        update.message.reply_text('[/announce]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['announceMsgNotFoundWarning'], quote=True)
        return
    else:
        msg = msg[1]

    context.user_data['command'] = '/announce'
    context.user_data['msg'] = msg

    keyboard = [
        [
            InlineKeyboardButton('翻譯組', callback_data=str(db.tg_chat_id['transTeamChatId']) + ' ' + user),
            InlineKeyboardButton('上字幕組', callback_data=str(db.tg_chat_id['subsTeamChatId']) + ' ' + user),
            InlineKeyboardButton('核對組', callback_data=str(db.tg_chat_id['checkingTeamChatId']) + ' ' + user),
        ],
        [
            InlineKeyboardButton('特別翻譯組', callback_data=str(db.tg_chat_id['specialTransTeamChatId']) + ' ' + user),
            InlineKeyboardButton('IT部', callback_data=str(db.tg_chat_id['itTeamChatId']) + ' ' + user),
            InlineKeyboardButton('Channel', callback_data=str(db.tg_chat_id['ttokbokkisubsChannelId']) + ' ' + user),
        ],
        [
            InlineKeyboardButton('SNS組', callback_data=str(db.tg_chat_id['snsTeamChatId']) + ' ' + user),
            InlineKeyboardButton('Cancel', callback_data='cancel ' + user)
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('@' + user + ' ' + db.reply_msg_json[db.bot_mode]['announceGroupQuery'], reply_markup=reply_markup, quote=True)
    return db.WAITING_ANNOUNCE


def button_announce(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user = query.from_user.username

    if user == query.data.split()[1] and 'command' in context.user_data and context.user_data['command'] == '/announce':
        # set new chat id
        targetChatId = query.data.split()[0]

        # cancel action
        if targetChatId == 'cancel':
            bot_funct.button_cancel(update, context, ' /announce 已取消')
            print('/announce 被取消咗')
            context.user_data.clear()
            return main.ConversationHandler.END

        if int(targetChatId) == db.tg_chat_id['itTeamChatId']:
            target = 'IT部'
        elif int(targetChatId) == db.tg_chat_id['transTeamChatId']:
            target = '翻譯組'
        elif int(targetChatId) == db.tg_chat_id['specialTransTeamChatId']:
            target = '特別翻譯組'
        elif int(targetChatId) == db.tg_chat_id['subsTeamChatId']:
            target = '上字幕組'
        elif int(targetChatId) == db.tg_chat_id['checkingTeamChatId']:
            target = '核對組'
        elif int(targetChatId) == db.tg_chat_id['ttokbokkisubsChannelId']:
            target = 'Channel'
        elif int(targetChatId) == db.tg_chat_id['snsTeamChatId']:
            target = 'SNS組'
        else:
            target = '???'

        bot_funct.button_cancel(update, context, ' message 已announce去 ' + target)
        print('Message from ' + user + ' announced')

        query.message.chat.id = targetChatId
        # message_id = query.message.message_id
        query.message.reply_text(context.user_data['msg'], quote=False)
        context.user_data.clear()
    return main.ConversationHandler.END
