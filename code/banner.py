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


def start_banner(update: Update, context: CallbackContext) -> int:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    if 'command' in context.user_data:
        bot_funct.multipleCommandMessage(update, context)
        update.message.reply_text('[' + context.user_data['command'] + ']: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['multipleCommandWarning'], quote=False)
        return main.ConversationHandler.END
    context.user_data['command'] = '/banner'
    print('/banner triggered by', user)
    context.user_data['current_conversation_message'] = [update.message, update.message.reply_text('[/banner]: @' + user + ' 呢條係咩片?\n請以"YYMMDD 片名"格式輸入\n/cancel 取消command', quote=True)]
    return db.GET_RESPONSE


def getNameListnMakeBanner(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user.username
    namelist_orig = update.message.text.splitlines()

    namelist_dict = {}
    new_position = True
    cur_position = ''
    for name in namelist_orig:
        if name == '':  # a separate line
            new_position = True
        elif new_position is True:  # position header
            new_position = False
            cur_position = name
            namelist_dict[cur_position] = []
        else:  # editors' names
            namelist_dict[cur_position].append(name)
    
    # Name list checking
    for position in namelist_dict:
        namelist = namelist_dict[position]
        partlist_str = bot_funct.checkPartlist(namelist)
        if partlist_str != 'Good':
            update.message.reply_text('[/banner]: @' + user + ' ' + partlist_str, quote=False)
            return

    color_red = r'{\1c&HB86EF3&\3c&HFFFFFF&\shad0}'
    color_pink = r'{\1c&HFFFFFF&\3c&HAD81F8&}'
    space2 = r'\h\h'
    space5 = r'\h\h\h\h\h'
    banner_prefix = r'{\pos(0,44)}本影片字幕及翻譯由' + color_pink + r' 辣炒年糕字幕組(ttokbokkisubs) {\r}製作，只供欣賞、娛樂及學習用途。' + space2 + r'未經許可，請勿二傳或二改' + space5  + color_pink + r'[製作名單]{\r}' + space2
    banner_postfix = r'辣炒年糕字幕組感謝大家一直以來的支持同鼓勵(ง •_•)ง' + space2 + r'希望嚟緊繼續再為大家服務٩(˃̶͈௰˂̶͈)و' + space5 + r'辣炒Instagram: ' + color_pink + r'ttokbokkisubs{\r}  Youtube/Dailymotion: ' + color_pink + r'ttokbokkisubs 辣炒年糕字幕組{\r}'
    # banner_postfix = space5 + r' 字幕組長期招新 歡迎大家加入一齊食辣炒年糕!!♡♡' + space2 + r'有意者請聯絡Instagram: ' + color_pink + r'ttokbokkisubs{\r}  Youtube/Dailymotion: ' + color_pink + r'ttokbokkisubs 辣炒年糕字幕組{\r}'
    banner = banner_prefix
    for position in namelist_dict:
        namelist = namelist_dict[position]
        name_str = ''
        for name in namelist:
            name_str += name + '  '
        banner += color_red + position + r':{\r}  ' + name_str + space5
    banner += banner_postfix

    update.message.delete()
    update.message.reply_text(banner, quote=False)
    bot_funct.DeleteConversationMessage(context.user_data['current_conversation_message'])
    context.user_data['current_conversation_message'] = []
    
    # post reminder to sns team
    if update.message.chat.id == db.tg_chat_id['subsTeamChatId']:  # subs
        print(context.user_data['videoName'] + ' is going to render, reminder sent to SNS team')
        update.message.chat.id = db.tg_chat_id['snsTeamChatId']  # sns
        update.message.reply_text('聽講剪接組已經準備要REN片, 快啲準備cover同出post! (ง •_•)ง\n\n呢條係{}\n參與名單:\n{}'.format(context.user_data['videoName'], '\n'.join(namelist_orig)), quote=False)
    context.user_data.clear()
    return main.ConversationHandler.END

