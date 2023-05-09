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


def reg_part(update: Update, context: CallbackContext) -> int:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    reply_message = update.message.reply_to_message
    print('/reg triggered by', user)

    # Check if /reg command replying message or not and is it replying the partlist
    if reply_message is None:
        update.message.reply_text('[/reg]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['replyNotFoundWarning'], quote=True)
        return
    elif not (reply_message.from_user.username == config.bot_username):
        update.message.reply_text('[/reg]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['notReplyingBotWarning'], quote=True)
        return
    elif '>>' in reply_message.text: # check if this list is a register list or a part divided namelist 
        update.message = reply_message
        update.message.reply_text('[/reg]: @' + user + ' sorry 呢個唔係報名表', quote=True)
        return

    namelist = reply_message.text.splitlines()
    new_text = update.message.text
    messagelist = new_text.split()

    if len(messagelist) < 3: # not enough argument
        update.message.reply_text('[/reg]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['invalidNamelistWarning'] + '\n格式: /reg [崗位(A,B...)][崗位第幾個(1,2..)] [你想叫咩名]', quote=True)
        return
    elif len(messagelist) > 4: # space in name
        update.message.reply_text('[/reg]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['nameSpacingWarning'], quote=True)
        return
    
    part_id = messagelist[1].upper()
    reg_name = messagelist[2]
    reg_time = ''
    try:
        if float(messagelist[3]) <= 0:
            update.message.reply_text('[/reg]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['nonPositiveTimeWarning'], quote=True)
            return
        else:
            reg_time = float(messagelist[3])
    except ValueError:
        update.message.reply_text('[/reg]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['nameSpacingWarning'], quote=True)
        return
    except IndexError: # no preserved time
        reg_time = ''
    print(user, 'reg part {} as {} , preserved time={}'.format(part_id, reg_name, reg_time))
    
    found = False
    isPartlist = False
    new_position = True
    cur_position = ''
    cnt = 0
    category = '\u0040'  # ASCII 64 (the one before 'A')
    title = namelist[0]
    for i in range(len(namelist)):
        name = namelist[i]
        if name[0:10] == '==========':
            isPartlist = not isPartlist
            continue
        if isPartlist:
            if name == '':  # a separate line
                new_position = True
            elif new_position is True:  # position header
                category = chr(ord(category) + 1)
                new_position = False
                cur_position = name
                cnt = 0
            else:  # editors' names
                cnt += 1

            # insert name to list
            if category == part_id[0]:
                if int(part_id[1:]) == 0:
                    continue
                elif name == '?': # first user to reg
                    namelist[i] = '{}-@{} {}'.format(reg_name, user, reg_time)
                    found = True
                    break
                elif cnt == int(part_id[1:]): # the position that user want to reg
                    namelist[i] = '{}-@{} {}'.format(reg_name, user, reg_time) + '\n' + name
                    found = True
                    break
                elif cnt+1 == int(part_id[1:]) and (namelist[i+1] in ['', '==========']): # append to list if the part_id is correct
                    namelist[i] = name + '\n' + '{}-@{} {}'.format(reg_name, user, reg_time)
                    found = True
                    break
    
    new_text = '\n'.join(namelist)
    
    if found == False:
        update.message.reply_text('[/reg]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['invalidPartIDWarning'], quote=True)
        return
    if new_text == reply_message.text:
        return
    reply_message.edit_text(text=new_text)
    update.message.delete()
    update.message = reply_message
    update.message.reply_text('[/reg]: {}-@{} 多謝你幫手做呀'.format(reg_name, user), quote=True)
    context.user_data.clear()
    
    return main.ConversationHandler.END
