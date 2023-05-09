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


def edit_msg(update: Update, context: CallbackContext) -> int:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    reply_message = update.message.reply_to_message
    title = reply_message.text.splitlines()[0]
    chat_id = reply_message.chat_id
    print('/edit triggered by', user)

    # Check if /edit command replying message or not and is it replying the partlist
    if reply_message is None:
        update.message.reply_text('[/edit]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['replyNotFoundWarning'], quote=True)
        return
    elif not (reply_message.from_user.username == config.bot_username):
        update.message.reply_text('[/edit]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['notReplyingBotWarning'], quote=True)
        return

    new_text = update.message.text

    # remove the command and only stores the text
    if len(new_text.split()) == 1:
        update.message = reply_message
        update.message.reply_text('[/edit]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['editMsgNotFoundWarning'], quote=True)
        return
    else:
        new_text = new_text[len('/edit') + 1:]

    print(user, 'edited message')

    if reply_message.text == new_text:
        update.message = reply_message
        update.message.reply_text('[/edit]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['sameEditMsgWarning'], quote=True)
        return 
    else:
        update.message.delete()
        
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

        new_text = bot_funct.update_progress(update, context, new_text)
        reply_message.edit_text(text=new_text)
        update.message = reply_message
        update.message.reply_text('[/edit]: @' + user + ' '+ db.reply_msg_json[db.bot_mode]['editSuccessNoti'], quote=True)
        context.user_data.clear()
    
    return main.ConversationHandler.END
