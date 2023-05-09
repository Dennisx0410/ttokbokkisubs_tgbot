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


def add_doc(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    print('/doc triggered by', user)
    reply_message = update.message.reply_to_message

    if reply_message is None:
        update.message.reply_text('[/doc]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['replyNotFoundWarning'], quote=True)
        return
    elif not (reply_message.from_user.username == config.bot_username):
        update.message.reply_text('[/doc]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['notReplyingBotWarning'], quote=True)
        return

    old_text = reply_message.text
    messagelist = old_text.splitlines()

    # check input
    if len(update.message.text.split()) <= 1:
        update.message.reply_text('[/doc]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['invalidInputWarning'], quote=True)
        return

    doc_link = update.message.text.split()[1]
    if 'docs.google.com' not in doc_link:
        update.message.reply_text('[/doc]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['invalidDoclinkWarning'], quote=True)
        return

    # check add new doc link or edit existing link
    if 'docs.google.com' in old_text: # already exist doc link
        separate_line = -1
        for k in range(len(messagelist)):
            if messagelist[k][0:10] == '==========':
                if separate_line != -1: # the second separate line
                    separate_line = k
                    break
                separate_line = k

        new_text = '\n'.join(messagelist[0:separate_line]) + '\n==========\n' + doc_link
        
        # check if the new text same as old text
        if new_text == old_text:
            update.message.delete()
            update.message = reply_message
            update.message.reply_text('[/doc]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['titleDulplicatedWarning'], quote=True)
            return

        reply_message.edit_text(text=new_text)
        update.message.delete()
        update.message = reply_message
        update.message.reply_text('[/doc]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['doclinkModifiedNoti'], quote=True)
    else:
        new_text = old_text + '\n==========\n' + doc_link
        reply_message.edit_text(text=new_text)
        update.message.delete()
        update.message = reply_message
        update.message.reply_text('[/doc]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['doclinkAddedNoti'], quote=True)
