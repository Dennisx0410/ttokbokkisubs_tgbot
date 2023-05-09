# libraries
import os
import sys
import requests
import signal
import random
import isodate
from datetime import datetime, date

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
import db


def info(update: Update, context: CallbackContext) -> None:
    if random_bot_mode(update, context) == db.END_TASK: return
    update.message.reply_text('{}\n{}\nLast update: {}\nBot mode: {}\nDev mode: {}'.format(main.toolName, main.authorMsg, main.lastUpdate, bot_description(db.bot_mode), db.dev_mode), quote=False) 


def updatenote(update: Update, context: CallbackContext) -> int:
    if random_bot_mode(update, context) == db.END_TASK: return
    updatenote_list = '''
-change: use webhook instead of polling
    '''
    update.message.reply_text('{}\n{}\nLast update: {}\nBot mode: {}\nDev mode: {}\n=========={}'.format(main.toolName, main.authorMsg, main.lastUpdate, bot_description(db.bot_mode), db.dev_mode, updatenote_list), quote=False)


def helpmenu(update: Update, context: CallbackContext) -> None:
    if random_bot_mode(update, context) == db.END_TASK: return
    command_list = '''
/newjob - 新增工作報名表
/reg - 報名
/divpart - 跟據片長或以keyword/URL搜尋影片並分part，回傳分好part嘅txt(如果有)
/banner - 產生aegisub banner
/title - reply名單加標題
/doc - reply名單加google doc
/edit - edit reply嘅bot message
/delete - delete reply嘅bot message
/done - reply名單講做完邊part
/undone - reply名單刪某part嘅tick
/announce - 用bot send message到自己擇嘅group
/closejob - 從進度表移除已完成工作
/info - bot資訊
/updatenote - 更新內容
/setting - set bot模式
/help - 睇bot有咩command'''
    update.message.reply_text(main.toolName + '\n' + main.authorMsg + '\nLast update: ' + main.lastUpdate + '\nBot mode: ' + bot_description(db.bot_mode) + '\n==========' + command_list, quote=False)


# welcome message for new incomers
def welcome(update: Update, context: CallbackContext) -> None:
    chat_room = update.message.chat
    new_chat_members = update.message.new_chat_members
    
    for member in new_chat_members:
        print('{} (@{}) joined {} (chatID={})'.format(member.full_name, member.username, chat_room.title, chat_room.id))
        update.message.reply_text('歡迎 {} (@{}) 加入 {}'.format(member.full_name, member.username, chat_room.title), quote=True)


# description of bot modes
def bot_description(bot_mode):
    if bot_mode == 'default':
        return '正常bot'
    elif bot_mode == 'evil':
        return '惡bot'
    elif bot_mode == 'sis':
        return '姐姐bot'
    elif bot_mode == 'gang':
        return '粗口bot'
    elif bot_mode == 'lolli':
        return '蘿莉bot'
    else:
        return '正常bot'


# radomize today's bot mode
def random_bot_mode(update: Update, context: CallbackContext) -> int:
    # check if the chat room is approved
    chat_room = update.message.chat
    user = update.message.from_user.username
    fullname = update.message.from_user.full_name
    chat_rooom_name = chat_room.title

    if chat_room.type == 'private':
        if user not in db.authorlist and user not in db.whitelist:
            update.message.reply_text(fullname + '你PM我無用㗎喎', quote=True)
            return db.END_TASK
    elif chat_room.id not in db.tg_chat_id.values():
        update.message.reply_text('sorry 呢度唔係我嘅工作範圍', quote=True)
        print('@{} sent message to bot in {} (chat_id={}) with message=\'{}\''.format(user, chat_room.title, chat_room.id, update.message.text))
        return db.END_TASK

    # random bot mode
    today = date.today()
    if today > db.bot_mode_last_update:
        db.bot_mode = random.choice(list(db.reply_msg_json.keys()))
        db.bot_mode_last_update = today
        print('today is ' + bot_description(db.bot_mode))


# delete message in chatroom
def DeleteConversationMessage(messages):
    for message in messages:
        message.delete()


# request user to input namelist
def requestNamelist(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    command = context.user_data['command']
    namelist_format = ' 請以以下格式輸入名單:\n職位1\n工作人員1\n工作人員N\n\n職位2\n工作人員1\n工作人員N\n...\n\n職位M\n工作人員1\n工作人員N\n'
    if 'current_conversation_message' in context.user_data:  # Record the conversation message
        context.user_data['current_conversation_message'].append(update.message.reply_text('[' + command + ']: @' + user + namelist_format + '\n/cancel 取消command', quote=False))
    else:
        context.user_data['current_conversation_message'] = [update.message.reply_text('[' + command + ']: @' + user + namelist_format + '\n/cancel 取消command', quote=False)]


def checkPartlist(namelist, total_time=0):
    total_time = int(total_time)
    preserved_namelist = list()
    preserved_timelist = list()
    if len(namelist) == 0:
        return db.reply_msg_json[db.bot_mode]['invalidNamelistWarning']
    for i in range(len(namelist)):
        if len(namelist[i].split()) == 2:
            try:
                if float(namelist[i].split()[1]) <= 0:
                    return db.reply_msg_json[db.bot_mode]['nonPositiveTimeWarning']
            except ValueError:
                return db.reply_msg_json[db.bot_mode]['nameSpacingWarning']
            preserved_namelist.append(namelist[i].split()[0])
            preserved_timelist.append(int(float(namelist[i].split()[1]) * 60))
        elif len(namelist[i].split()) > 2:
            return db.reply_msg_json[db.bot_mode]['invalidNamelistWarning']
    if sum(preserved_timelist) > total_time:
        return db.reply_msg_json[db.bot_mode]['invalidPreservedLengthWarning']
    return 'Good'


def update_progress(update: Update, context: CallbackContext, orig_text):
    reply_message = update.message.reply_to_message
    title = orig_text.splitlines()[0]
    chat_id = update.message.chat_id
    if '>>' not in orig_text:
        return orig_text

    done_people = 0
    total_people = 0
    messagelist = orig_text.splitlines()

    # parse messagelist into partlist and namelist_dict
    def parse_messagelist(messagelist):
        isPartlist = False
        new_position = True
        cur_position = ""
        position_line_no = 0
        done_people = 0
        total_people = 0
        partlist_dict = {}
        for i in range(len(messagelist)):
            line = messagelist[i]
            if line[0:10] == '==========':
                isPartlist = not isPartlist
                continue
            if isPartlist:
                if line == '':  # a separate line
                    partlist_dict[cur_position]["done_count"] = done_people
                    partlist_dict[cur_position]["total_count"] = total_people
                    
                    messagelist[position_line_no] = messagelist[position_line_no].split()[0] + ' ({}/{})'.format(done_people, total_people)
                    new_position = True
                elif new_position is True:  # position header
                    done_people = 0
                    total_people = 0
                    position_line_no = i
                    new_position = False
                    cur_position = line.split()[0]
                    partlist_dict[cur_position] = {
                        "done_count" : done_people,
                        "total_count" : total_people,
                        "part" : []
                    }
                elif '>>' not in line:
                    part_editor = line
                    if db.unicodeTick in line:  # editors' names
                        done_people += 1
                    total_people += 1
                elif '>>' in line:
                    part_time = line
                    part = {
                        "editor" : part_editor.replace(db.unicodeTick, ''), 
                        "time" : part_time, 
                        "ticks" : part_editor.count(db.unicodeTick)
                    }

                    partlist_dict[cur_position]["part"].append(part)

        partlist_dict[cur_position]["done_count"] = done_people
        partlist_dict[cur_position]["total_count"] = total_people
        messagelist[position_line_no] = messagelist[position_line_no].split()[0] + ' ({}/{})'.format(done_people, total_people)
        return messagelist, partlist_dict, done_people, total_people

    messagelist, partlist_dict, done_people, total_people = parse_messagelist(messagelist)

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

        # add new job to progresslist
        if title not in db.progresslist:
            db.progresslist[title] = []

        db.progresslist[title].append({
            "chat_id" : reply_message.chat_id, 
            "message_id" : reply_message.message_id, 
            "namelist" : partlist_dict
        })    
        
        fileio.writeJson("progress.json", db.progresslist)
        show_progress(update, context)

    return '\n'.join(messagelist)


def show_progress(update: Update, context: CallbackContext):
    # progress list
    db.progresslist = fileio.readJson("progress.json")

    target_chat_id = db.progresslist["channel_id"]
    target_message_id = db.progresslist["message_id"]

    update.message.chat.id = target_chat_id
    update.message.message_id = target_message_id

    progresslist = []
    progresslist_str = ""

    try:
        context.bot.deleteMessage(target_chat_id, target_message_id)
    except:
        print("message does not exist")

    for title in db.progresslist:
        progress_str = ""
        if title not in ["channel_id", "message_id"]:
            progress_str += title + '\n'
            for message_dict in db.progresslist[title]:
                for position in message_dict["namelist"]:
                    info = message_dict["namelist"][position]
                    if info["done_count"] == info["total_count"]:
                        progress_str += '-{} DONE\n'.format(position)
                    else:
                        progress_str += '-{} ({}/{})\n'.format(position, info["done_count"], info["total_count"])
            progresslist_str += progress_str + '\n'

    if len(progresslist_str) > 0:
        now = datetime.now()
        current_time = now.strftime("%y%m%d %H:%M:%S")
        update_latest = update.message.reply_text("<進度表> 更新時間: {}\n註: \n本進度表由botbot自動產生, 請勿更改。\n現於測試階段, 有機會唔準\n==========\n{}".format(current_time, progresslist_str), quote=False)
        db.progresslist["message_id"] = update_latest["message_id"]
        fileio.writeJson("progress.json", db.progresslist)

def button_cancel(update: Update, context: CallbackContext, msg) -> int:
    query = update.callback_query
    query.answer()

    if 'command' in context.user_data:
        # clear inline-keyboard
        keyboard = [[]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text('@' + query.from_user.username + msg, reply_markup=reply_markup)
        # return main.ConversationHandler.END


def getVidName(update: Update, context: CallbackContext) -> int:
    if random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    chat_id = update.message.chat.id
    context.user_data['videoName'] = update.message.text    
    if context.user_data['command'] == '/newjob':        
        if chat_id in [db.tg_chat_id['transTeamChatId'], db.tg_chat_id['specialTransTeamChatId']]:  # trans
            position1 = "翻譯"
            position2 = "韓核"
        elif chat_id == db.tg_chat_id['subsTeamChatId']:  # subs
            position1 = "軸仔"
            position2 = "軸核"
        else: 
            position1 = "翻譯/軸仔"
            position2 = "核對"
        update.message.reply_text(''' 
        {} 報名表
==========
{}
?

{}
?
==========
請用 /reg 嚟報名, reply 本報名表
格式: /reg [崗位(A,B...)][崗位第幾個(1,2..)] [你想叫咩名] [你想做嘅分鐘(optional)]
如: /reg A2 juice 3 或 /reg B1 TL 
        '''.format(context.user_data['videoName'], position1, position2), quote=False).pin()
        DeleteConversationMessage(context.user_data['current_conversation_message'])
        context.user_data['current_conversation_message'] = []
        update.message.delete()
        context.user_data.clear()
        return main.ConversationHandler.END
    elif context.user_data['command'] == '/banner':
        DeleteConversationMessage(context.user_data['current_conversation_message'])
        context.user_data['current_conversation_message'] = []
        update.message.delete()

        requestNamelist(update, context)
        return db.GET_NAMELIST

def cancel(update: Update, context: CallbackContext) -> int:
    if random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    if 'command' in context.user_data:
        update.message.reply_text('@' + user + ' ' + context.user_data['command'] + ' ' + db.reply_msg_json[db.bot_mode]['cancelSuccessNoti'], quote=False)
        print(context.user_data['command'], 'is cancelled')
        if 'current_conversation_message' in context.user_data:
            DeleteConversationMessage(context.user_data['current_conversation_message'])
        if 'video_message' in context.user_data:
            DeleteConversationMessage(context.user_data['video_message'])
        context.user_data.clear()
        return main.ConversationHandler.END
    else:
        update.message.reply_text('@' + user + ' ' + db.reply_msg_json[db.bot_mode]['cancelCommandNotFoundWarning'], quote=False)


def invalidTimeMessage(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    command = context.user_data['command']
    update.message.reply_text('[' + command + ']: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['invalidTimeFormatWarning'], quote=False)


def multipleCommandMessage(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user.username
    command = context.user_data['command']
    print(command)
    update.message.reply_text('@{} 你之前call咗 {}\n{}'.format(user, command, db.reply_msg_json[db.bot_mode]['multipleCommandWarning']), quote=True)


def timeout(update: Update, context: CallbackContext) -> int:
    if 'command' in context.user_data:
        update.message.reply_text('@' + update.message.from_user.username + ' ' + context.user_data['command'] + ' ' + db.reply_msg_json[db.bot_mode]['timeoutNoti'], quote=False)
        del context.user_data['command']
        

def kill(update: Update, context: CallbackContext) -> int:
    if random_bot_mode(update, context) == db.END_TASK: return
    print('/kill triggered by', update.message.from_user.username)
    update.message.reply_text('Bot server shutdown!', quote=False)
    fileio.writeJson('credential.json', db.cred_json)
    os.kill(os.getpid(), signal.SIGINT)
    return main.ConversationHandler.END