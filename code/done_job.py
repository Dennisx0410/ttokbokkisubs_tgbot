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

# code files
import main
import config
import fileio
import functions as bot_funct
import db

def done_job(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    reply_message = update.message.reply_to_message
    chat_id = update.message.chat.id
    print('/done triggered by', user)

    # Check if /done command replying message or not and is it replying the partlist
    if reply_message is None:
        update.message.reply_text('[/done]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['replyNotFoundWarning'], quote=False)
        return
    elif not (reply_message.from_user.username == config.bot_username):
        update.message.reply_text('[/done]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['notReplyingBotWarning'], quote=False)
        return

    old_text = reply_message.text
    part_id = update.message.text.split()[1:]
    part_id = [ID.lower() for ID in part_id]

    # remove the command and only stores the text
    if (len(part_id) <= 0):
        update.message.reply_text('[/done]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['partIDNotFoundWarning'], quote=False)
        return

    # Find position and number
    def tickmessagebypartid(messagelist, part_id='', tickall=False):
        messagelist = messagelist.splitlines()
        pos, num = ord('a'), 1
        if tickall is False:
            if not ('a' <= part_id[0] <= 'z'):
                update.message.reply_text('[/done]: @' + user + ' ' + part_id + ' ' + db.reply_msg_json[db.bot_mode]['invalidPartIDWarning'], quote=False)
                return False, 'invalid', ''
            try:
                num = int(part_id[1:])
            except ValueError:
                update.message.reply_text('[/done]: @' + user + ' ' + part_id + ' ' + db.reply_msg_json[db.bot_mode]['invalidPartIDWarning'], quote=False)
                return False, 'invalid', ''
            if 'a' <= part_id[0] <= 'z':
                pos = ord(part_id[0]) - ord('a')

        i = 1
        for k in range(len(messagelist)):
            if messagelist[k][0:10] == '==========':
                i = k + 2
                break
        j = 1
        ordi = 0
        name = False
        while(i < len(messagelist)):
            if messagelist[i] == '':
                ordi = (ordi + 1) % 26
                j = 1
            elif messagelist[i][0:10] == '==========':
                break
            elif '>>' not in messagelist[i] and messagelist[i - 1] != '':
                if tickall is True:
                    messagelist[i] = ''.join([char for char in messagelist[i] if char != db.unicodeTick]) + db.unicodeTick
                elif (ordi, j) == (pos, num):
                    name = messagelist[i]
                    messagelist[i] += db.unicodeTick
                    new_text = '\n'.join(messagelist)
                    donepart = messagelist[i + 1]
                    if ordi == 1: # B stands for checking
                        name += db.unicodeTick
                    return new_text, name, donepart

                j += 1
            i += 1
        if tickall is True:
            new_text = '\n'.join(messagelist)
            return new_text
        return False, part_id, ''

    def alldone(messagelist):
        messagelist = messagelist.splitlines()
        i = 1
        for k in range(len(messagelist)):
            if messagelist[k][0:10] == '==========':
                i = k + 2
                break
        total_people = [0]  # [position1, position2, ...]
        ticked_people = [0]  # [position1, position2, ...]
        total_tick = [0]  # [position1, position2, ...]
        pos = 0
        while(i < len(messagelist)):
            if messagelist[i] == '':
                total_people.append(0)
                ticked_people.append(0)
                total_tick.append(0)
                pos += 1
            elif messagelist[i][0:10] == '==========':
                break
            elif '>>' not in messagelist[i] and messagelist[i - 1] != '':
                if db.unicodeTick in messagelist[i]:
                    ticked_people[pos] += 1
                    total_tick[pos] += messagelist[i].count(db.unicodeTick)
                total_people[pos] += 1
            i += 1
        state_list = list()
        for position in range(pos + 1):
            if ticked_people[position] == total_people[position]:  # make sure all part ticked but not include 核對tick
                if total_tick[position] == total_people[position] * 2:
                    state_list.append('alldoubletick')
                else:
                    state_list.append('alltick')
            else:
                state_list.append('notdone')
        return state_list

    def getTitle(messagelist):
        messagelist = messagelist.splitlines()
        for k in range(len(messagelist)):
            if messagelist[k][0:10] == '==========':
                return messagelist[k - 1]
        return 'yymmdd 冇標題'

    # if /done all triggered, tick all name once
    if 'all' in part_id:
        new_text = tickmessagebypartid(old_text, tickall=True)
        new_text = bot_funct.update_progress(update, context, new_text)
        reply_message.edit_text(text=new_text)
        update.message.chat.id = chat_id
        update.message.reply_text('[/done]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['alltickedNoti'], quote=False)
        return

    new_text = old_text
    namelist = list()  # finish name list
    donepartlist = list()  # done part list
    checklist = list()  # checking part name list
    unfoundlist = list()  # unfound part id list
    for ID in part_id:
        tmp_text, name, donepart = tickmessagebypartid(old_text, ID)
        if tmp_text:  # to keep old_test is valid text not False
            old_text = tmp_text
        if tmp_text is not False:
            if db.unicodeTick in name:
                new_text = old_text
                checklist.append(name.replace(db.unicodeTick, ''))
            else:
                new_text = old_text
                namelist.append(name)
                donepartlist.append(donepart)
        elif name != 'invalid':
            unfoundlist.append(name)

    title = getTitle(new_text)
    progress = alldone(new_text)
    
    # trans and subs
    if len(namelist) > 0:
        update.message.chat.id = chat_id
        update.message.reply_text('[/done]: ' + ', '.join(namelist) + ' ' + db.reply_msg_json[db.bot_mode]['partDoneAndThanksNoti'] + ' @' + user, quote=False)
        if progress[0] != 'alltick':  # if not all done, notify the part to checking team which have finished
            if chat_id in [db.tg_chat_id['transTeamChatId'], db.tg_chat_id['specialTransTeamChatId']]:  # trans
                update.message.chat.id = db.tg_chat_id['checkingTeamChatId']  # checking
                update.message.reply_text('[/done]: ' + title + '\n==========\n' + ', '.join(namelist) + ' ' + db.reply_msg_json[db.bot_mode]['transPartDoneNoti'] + '\n' + '\n'.join(donepartlist) + '\n', quote=False)
            elif chat_id == db.tg_chat_id['subsTeamChatId']:  # subs
                update.message.chat.id = db.tg_chat_id['checkingTeamChatId']  # checking
                update.message.reply_text('[/done]: ' + title + '\n==========\n' + ', '.join(namelist) + ' ' + db.reply_msg_json[db.bot_mode]['subsPartDoneNoti'] + '\n' + '\n'.join(donepartlist) + '\n', quote=False)
        else:
            if chat_id in [db.tg_chat_id['transTeamChatId'], db.tg_chat_id['specialTransTeamChatId']] :  # trans
                update.message.chat.id = db.tg_chat_id['checkingTeamChatId']  # checking
                update.message.reply_text('[/done]: ' + title + '\n==========\n' + db.reply_msg_json[db.bot_mode]['transTeamDoneNoti'], quote=False)
            elif chat_id == db.tg_chat_id['subsTeamChatId']:  # subs
                update.message.chat.id = db.tg_chat_id['checkingTeamChatId']  # checking
                update.message.reply_text('[/done]: ' + title + '\n==========\n' + db.reply_msg_json[db.bot_mode]['subsTeamDoneNoti'], quote=False)
    
    # checking team
    if len(checklist) > 0:
        update.message.chat.id = chat_id
        update.message.reply_text('[/done]: ' + ', '.join(checklist) + ' ' + db.reply_msg_json[db.bot_mode]['checkDoneAndThanksNoti'] +' @' + user, quote=False)
        if progress[1] == 'alltick' or progress[0] == 'alldoubletick':  # checking team done all by double tick or tick own part
            if chat_id in [db.tg_chat_id['transTeamChatId'], db.tg_chat_id['specialTransTeamChatId']]:  # trans
                update.message.chat.id = db.tg_chat_id['subsTeamChatId']  # subs
                update.message.reply_text('[/done]: ' + title + '\n==========\n' + db.reply_msg_json[db.bot_mode]['transCheckTeamDoneNoti'], quote=False)
            elif chat_id == db.tg_chat_id['subsTeamChatId']:  # subs
                update.message.chat.id = db.tg_chat_id['subsTeamChatId']  # subs
                update.message.reply_text('[/done]: ' + title + '\n==========\n' + db.reply_msg_json[db.bot_mode]['subsCheckTeamDoneNoti'], quote=False)
            
            # remove scheduled reminder
            try:
                joblist = context.chat_data[title]

                # single reminder
                job = joblist
                job.schedule_removal()
                print('scheduled reminder message removed')
            except Exception:
                print('scheduled reminder does not exist')
        else:  # checking team only finished some of the parts
            if chat_id in [db.tg_chat_id['transTeamChatId'], db.tg_chat_id['specialTransTeamChatId']]:  # trans
                update.message.chat.id = db.tg_chat_id['subsTeamChatId']  # subs
                update.message.reply_text('[/done]: ' + title + '\n==========\n' + ', '.join(checklist) + ' ' + db.reply_msg_json[db.bot_mode]['transCheckPartDoneNoti']+ '\n' + donepart, quote=False)

    if len(unfoundlist) > 0:
        update.message.chat.id = chat_id
        update.message.reply_text('[/done]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['partNotFoundWarning'].format(', '.join(unfoundlist)), quote=False)
    if new_text != reply_message.text:
        update.message.chat.id = chat_id
        new_text = bot_funct.update_progress(update, context, new_text)
        reply_message.edit_text(text=new_text)


def undone_job(update: Update, context: CallbackContext) -> None:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    chat_id = update.message.chat.id
    print('/undone triggered by', user)
    reply_message = update.message.reply_to_message

    # Check if /done command replying message or not and is it replying the partlist
    if reply_message is None:
        update.message.reply_text('[/undone]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['replyNotFoundWarning'], quote=False)
        return
    elif not (reply_message.from_user.username == config.bot_username):
        update.message.reply_text('[/undone]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['notReplyingBotWarning'], quote=False)
        return

    old_text = reply_message.text
    part_id = update.message.text.split()[1:]
    part_id = [ID.lower() for ID in part_id]

    # remove the command and only stores the text
    if (len(part_id) <= 0):
        update.message.reply_text('[/undone]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['partIDNotFoundWarning'], quote=False)
        return

    # Find position and number
    def untickmessagebypartid(messagelist, part_id=''):
        messagelist = messagelist.splitlines()
        pos, num = ord('a'), 1
        if not ('a' <= part_id[0] <= 'z'):
            update.message.reply_text('[/undone]: @' + user + ' ' + part_id + ' ' + db.reply_msg_json[db.bot_mode]['invalidPartIDWarning'], quote=False)
            return False, 'invalid'
        try:
            num = int(part_id[1:])
        except ValueError:
            update.message.reply_text('[/undone]: @' + user + ' ' + part_id + ' ' + db.reply_msg_json[db.bot_mode]['invalidPartIDWarning'], quote=False)
            return False, 'invalid'
        if 'a' <= part_id[0] <= 'z':
            pos = ord(part_id[0]) - ord('a')

        i = 1
        for k in range(len(messagelist)):
            if messagelist[k][0:10] == '==========':
                i = k + 2
                break
        j = 1
        ordi = 0
        name = False
        while(i < len(messagelist)):
            if messagelist[i] == '':
                ordi = (ordi + 1) % 26
                j = 1
            elif messagelist[i][0:10] == '==========':
                break
            elif '>>' not in messagelist[i] and messagelist[i - 1] != '':
                if (ordi, j) == (pos, num):
                    if db.unicodeTick in messagelist[i]:
                        name = ''.join([char for char in messagelist[i] if char != db.unicodeTick])
                        messagelist[i] = messagelist[i][:len(messagelist[i]) - 1]  # delete the last tick
                        new_text = '\n'.join(messagelist)
                        return new_text, name
                    else:
                        name = messagelist[i]
                        update.message.reply_text('[/undone]: @' + user + ' ' + name + ' ' + db.reply_msg_json[db.bot_mode]['tickNotFoundWarning'], quote=False)
                        return False, 'notick'
                j += 1
            i += 1
        return False, part_id

    # if /undone all triggered than clear all tick from the old message
    if 'all' in part_id:
        new_text = old_text.replace(db.unicodeTick, '')
        if new_text != old_text:
            new_text = bot_funct.update_progress(update, context, new_text)
            update.message.chat.id = chat_id
            reply_message.edit_text(text=new_text)
            update.message.reply_text('[/undone]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['alltickDeletedNoti'], quote=False)
        else:
            update.message.reply_text('[/undone]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['tickNotFoundWarning'], quote=False)
        return

    namelist = list()
    unfoundlist = list()
    for ID in part_id:
        tmp_text, name = untickmessagebypartid(old_text, ID)
        if tmp_text:
            old_text = tmp_text
        if tmp_text is not False:
            new_text = old_text
            namelist.append(name)
        elif name != 'invalid' and name != 'notick':
            unfoundlist.append(name)
    if len(namelist) > 0:
        new_text = bot_funct.update_progress(update, context, new_text)
        update.message.chat.id = chat_id
        reply_message.edit_text(text=new_text)
        update.message.reply_text('[/undone]: @' + user + ' ' + ' '.join(namelist) + ' ' + db.reply_msg_json[db.bot_mode]['tickDeletedNoti'], quote=False)
    if len(unfoundlist) > 0:
        update.message.reply_text('[/undone]: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['partNotFoundWarning'].format(', '.join(unfoundlist)), quote=False)