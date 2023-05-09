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


def start_closejob(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    print('/closejob triggered by', user)

    if 'command' in context.user_data:
        return bot_funct.multipleCommandMessage(update, context)

    context.user_data['command'] = '/closejob'

    # array of button
    keyboard = [[]]
    keyboard_btn = []
    titlecount = 0
    # progress list
    db.progresslist = fileio.readJson("progress.json")
    for title in db.progresslist:
        if title not in ["channel_id", "message_id"]:
            keyboard_btn.append(InlineKeyboardButton(title, callback_data=str(titlecount) + ' ' + user))
            titlecount += 1

    btnPerLine = 1
    btn_start = 0
    btn_end = btnPerLine
    for i in range(len(keyboard_btn) // btnPerLine + 1):
        keyboard.append(keyboard_btn[btn_start:btn_end])
        btn_start += btnPerLine
        btn_end += btnPerLine
    
    keyboard.append([InlineKeyboardButton('Cancel', callback_data='cancel ' + user)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('@' + user + ' 請問想將邊條片從進度表移除?', reply_markup=reply_markup, quote=True)
    return db.WAITING_SETTING
    

def button_closejob(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user = query.from_user.username
    
    if user == query.data.split()[-1] and 'command' in context.user_data and context.user_data['command'] == '/closejob':
        # set new chat id
        target = ' '.join(query.data.split()[:-1])
        print(target)

        # cancel action
        if target == 'cancel':
            bot_funct.button_cancel(update, context, ' /closejob 已取消')
            print('/closejob 被取消咗')

            context.user_data.clear()
            return main.ConversationHandler.END

        # progress list
        db.progresslist = fileio.readJson("progress.json")
        titlecount = 0
        # remove job from progresslist
        for title in db.progresslist:
            if str(titlecount) == target and title not in ["channel_id", "message_id"]:
                completed = True
                for message_dict in db.progresslist[title]:
                    for position in message_dict["namelist"]:
                        info = message_dict["namelist"][position]
                        if info["done_count"] != info["total_count"]:
                            completed = False
                if completed == False:
                    bot_funct.button_cancel(update, context, ' sorry 呢條 ' + title + ' 仲有人未做完')
                    context.user_data.clear()
                    return main.ConversationHandler.END
                else:
                    del db.progresslist[title]
                    break
            if title not in ["channel_id", "message_id"]:
                titlecount += 1

        bot_funct.button_cancel(update, context, ' ' + title + ' 已從進度表移除')
        print(user + ' removed ' + title + ' from progresslist')    

        update.callback_query.message.chat.id = db.tg_chat_id['itTeamChatId'] # it
        update.callback_query.message.reply_text('@' + user + ' 將 ' + title + ' 從進度表移除', quote=False)
        
        fileio.writeJson("progress.json", db.progresslist)
        bot_funct.show_progress(update.callback_query, context) 
        context.user_data.clear()
    return main.ConversationHandler.END
