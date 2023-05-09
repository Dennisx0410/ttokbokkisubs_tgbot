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


def delete_msg(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    chat_id = update.message.chat_id
    print('/delete triggered by', user)
    reply_message = update.message.reply_to_message
    title = reply_message.text.splitlines()[0]

    if reply_message is None:
        update.message.reply_text('[/delete]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['replyNotFoundWarning'], quote=False)
        return
    elif not (reply_message.from_user.username == config.bot_username):
        update.message.reply_text('[/delete]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['notReplyingBotWarning'], quote=False)
        return

    # delete user command request and chosen message
    reply_message.delete()
    update.message.delete()
    
    if chat_id != db.tg_chat_id['itTeamChatId'] and update.message.chat.type != "private":
        # progress list
        db.progresslist = fileio.readJson("progress.json")

        # del original job in progresslist
        if title in db.progresslist:
            for part_no in range(len(db.progresslist[title])):
                message = db.progresslist[title][part_no]
                if message["chat_id"] == chat_id and message["message_id"] == reply_message["message_id"]:
                    if len(db.progresslist[title]) == 1:
                        del db.progresslist[title]
                    else:
                        del db.progresslist[title][part_no]
                    break

        fileio.writeJson("progress.json", db.progresslist)
        bot_funct.show_progress(update, context)

    print(user + ' deleted a message')