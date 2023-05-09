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


def add_title(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    chat_id = update.message.chat_id
    print('/title triggered by', user)
    reply_message = update.message.reply_to_message

    if reply_message is None:
        update.message.reply_text('[/title]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['replyNotFoundWarning'], quote=True)
        return
    elif not (reply_message.from_user.username == config.bot_username):
        update.message.reply_text('[/title]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['notReplyingBotWarning'], quote=True)
        return

    old_text = reply_message.text
    messagelist = old_text.splitlines()

    # check for empty title
    if len(update.message.text.split(' ', 1)) <= 1:
        update.message.reply_text('[/title]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['titleNotFoundWarning'], quote=True)
        return

    title = update.message.text.split(' ', 1)[1]
    separate_line = -1
    for k in range(len(messagelist)):
        if messagelist[k][0:10] == '==========':
            separate_line = k
            break
    
    # delete user command request
    update.message.delete()

    if chat_id != db.tg_chat_id['itTeamChatId'] and update.message.chat.type != "private":
        # progress list
        db.progresslist = fileio.readJson("progress.json")

        title_old = old_text.splitlines()[0]
        # del original job in progresslist
        if title_old in db.progresslist:
            for part_no in range(len(db.progresslist[title_old])):
                message = db.progresslist[title_old][part_no]
                if message["chat_id"] == chat_id and message["message_id"] == reply_message["message_id"]:
                    if len(db.progresslist[title_old]) == 1:
                        del db.progresslist[title_old]
                    else:
                        del db.progresslist[title_old][part_no]
                    break

        fileio.writeJson("progress.json", db.progresslist)
        # bot_funct.show_progress(update, context)

    new_text = title + '\n' + '\n'.join(messagelist[separate_line:])
    new_text = bot_funct.update_progress(update, context, new_text)

    # check if the new text same as old text
    if new_text == old_text:
        update.message = reply_message
        update.message.reply_text('[/title]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['titleDulplicatedWarning'], quote=True)
        return

    reply_message.edit_text(text=new_text)
    update.message = reply_message
    update.message.reply_text('[/title]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['titleModifiedNoti'], quote=True)
