# libraries
import os
import requests
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
import functions as bot_funct
import db


# time foramt
def timeFormat(length):  # from length(sec) to the format of hh:mm:ss:sss
    sec, milis = divmod(length, 1)
    min, sec = divmod(sec, 60)
    hrs, min = divmod(min, 60)
    milis = round((milis + 1e-8) * 1000)

    return (hrs, min, sec, milis)


# second to mm:ss
def sectotime(length):
    hrs, min, sec, milis = timeFormat(length)
    return '%02d:%02d' % (min, sec)


def start_divpart(update: Update, context: CallbackContext) -> int:
    if bot_funct.random_bot_mode(update, context) == db.END_TASK: return
    user = update.message.from_user.username
    if 'command' in context.user_data:
        bot_funct.multipleCommandMessage(update, context)
        return main.ConversationHandler.END
    context.user_data['command'] = '/divpart'
    print('/divpart triggered by', user)
    context.user_data['current_conversation_message'] = [update.message, update.message.reply_text('[/divpart]: @' + user + '''
請輸入以下其中一種資料嚟分part: 
-影片嘅keyword
-URL
-片長(mm:ss)
/cancel 取消command
    ''', quote=True)]
    return db.GET_KEYWORDorURL


# divpart by input length
def getVidLen(update: Update, context: CallbackContext) -> int:
    mins, secs = list(map(int, update.message.text.split(':')))
    context.user_data['videolen'] = mins * 60 + secs
    context.user_data['title'] = 'yymmdd 冇標題'
    bot_funct.DeleteConversationMessage(context.user_data['current_conversation_message'])
    context.user_data['current_conversation_message'] = []
    update.message.delete()
    bot_funct.requestNamelist(update, context)
    return db.GET_NAMELIST


# divpart by input keyword or URL
def getKeywordOrURL(update: Update, context: CallbackContext) -> int:
    keyword = update.message.text
    user = update.message.from_user.username
    command = context.user_data['command']
    url, title, videolen = getVidLenFromYt(keyword)
    if (url, title, videolen) != (0, 0, 0):
        videoInfo = '[' + command + ']: @' + user + ' ' + url + ' \n' + title + '\n片長: ' + sectotime(int(videolen))
        if command == '/divpart':
            context.user_data['url'] = url
            srt = getSrt(update, context.user_data['url'])
            if srt is False:  # no srt
                videoInfo += '\n呢條片冇英文字幕!ಠ_ಠ'
            else:
                context.user_data['srt'] = srt
        bot_funct.DeleteConversationMessage(context.user_data['current_conversation_message'])
        context.user_data['current_conversation_message'] = []
        update.message.delete()
        context.user_data['video_message'] = [update.message.reply_text(videoInfo, quote=False)]
        context.user_data['title'] = title
        context.user_data['videolen'] = videolen
        bot_funct.requestNamelist(update, context)
        return db.GET_NAMELIST
    else:
        update.message.reply_text('[' + command + ']: @' + user + ' ' + db.reply_msg_json[db.bot_mode]['invalidTimeFormatOrKeywordWarning'], quote=False)
        return db.GET_KEYWORDorURL


def getSrt(update, url):
    srt = None
    try:
        srt = YouTubeTranscriptApi.get_transcript(url[-11:], languages=['en'])  # list of subtitle
        return createSrtList(srt)
    except Exception:
        return False


def createSrtList(srt):
    cnt = 0
    for sub in srt:
        cnt += 1
        subStartTime = sub['start']
        duration = sub['duration']
        subEndTime = subStartTime + duration
        sub['end'] = subEndTime
        sub['subID'] = cnt
    return srt


# Get video url, title, length by keywords or URL
def getVidLenFromYt(video):
    title = ''
    izone_channel_ID = 'UCe_oTYByLWQYCUmgmOMU_xw'
    if 'http://' not in video and 'https://' not in video and 'youtu.be/' not in video and 'youtube.com/' not in video:
        while(True):
            try:
                response = requests.get('https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=' + izone_channel_ID + '&order=relevance&maxResults=1&q=' + video + '&type=video&key=' + config.youtube_data_api_key)
                break
            except Exception:
                print('Connection Error during getVideolength! Reconnecting...')
        response_js = response.json()
        if 'items' in response_js and len(response_js['items']) > 0:
            video = response_js['items'][0]['id']['videoId']
            title = response_js['items'][0]['snippet']['title']
            publishedAtStr = response_js['items'][0]['snippet']['publishedAt']
            publishedDate = datetime.strptime(publishedAtStr, r'%Y-%m-%dT%H:%M:%SZ')
            publishedYYMMDD = publishedDate.strftime(r'%y%m%d')
            title = publishedYYMMDD + ' ' + editVidTitle(title)
        else:
            return 0, 0, 0
    else:
        if 'youtu.be/' in video:
            video = video[video.find('.be/') + 4: video.find('.be/') + 15]
        elif 'youtube.com' in video:
            video = video[video.find('?v=') + 3: video.find('?v=') + 14]

    while(True):
        try:
            response = requests.get('https://www.googleapis.com/youtube/v3/videos?id=' + video + '&part=snippet&part=contentDetails&key=' + config.youtube_data_api_key)
            break
        except Exception:
            print('Connection Error during getVideolength! Reconnecting...')
    response_js = response.json()
    if title == '':
        title = response_js['items'][0]['snippet']['title']
        publishedAtStr = response_js['items'][0]['snippet']['publishedAt']
        publishedDate = datetime.strptime(publishedAtStr, r'%Y-%m-%dT%H:%M:%SZ')
        publishedYYMMDD = publishedDate.strftime(r'%y%m%d')
        title = publishedYYMMDD + ' ' + editVidTitle(title)
    duration = isodate.parse_duration(response_js['items'][0]['contentDetails']['duration']).total_seconds()
    return 'https://youtu.be/' + video, title, duration


# edit video title prevent reserved symbols and shorten the title
def editVidTitle(title):
    html_char = {'&#39;' : '\'', '&#34;' : '\"', '&#38;' : '&', '&#60;' : '<', '&#62;' : '>'}
    for char in html_char:
        if char in title:
            title = title.replace(char, html_char[char])

    # special handle for ENOZI Cam, ENOZI Cam+, Arcade II
    if 'IZ*ONE 에너지 캠 플러스(ENOZI Cam +)' in title:
        title = title.replace('IZ*ONE 에너지 캠 플러스(ENOZI Cam +)', 'ENOZI Cam+')
        print(title)
    elif 'IZ*ONE 에너지 캠(ENOZI Cam)' in title:
        title = title.replace('IZ*ONE 에너지 캠(ENOZI Cam)', 'ENOZI Cam')
    elif 'IZ*ONE 아케이드Ⅱ (ARCADE Ⅱ)' in title:
        title = title.replace('IZ*ONE 아케이드Ⅱ (ARCADE Ⅱ)', 'Arcade Ⅱ')
    
    return title 


# parse the namelist and split time into parts
def getNamelistnSplitTime(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user.username
    chat_id = update.message.chat_id
    title = context.user_data['title']
    command = context.user_data['command']
    namelist_orig = update.message.text.splitlines()

    # check if partlist with same title already exist
    db.progresslist = fileio.readJson("progress.json")
    if title in db.progresslist:
        for message in db.progresslist[title]:
            if message["chat_id"] == chat_id:
                while title in db.progresslist:
                    title = title + "-new"
                update.message.reply_text('[/divpart]: @' + user + ' 已經有同名嘅partlist嗱喎, 你check多次? 我會幫你命名為' + title, quote=False)
                break

    partlist_dict = {}
    
    # parse namelist into namelist_dict and taglist_dict
    def parse_namelist(namelist):
        namelist_dict = {}
        tag_list = []
        new_position = True
        cur_position = ''
        cnt = 0
        category = '\u0040'  # ASCII 64 (the one before 'A')
        for name in namelist:
            if name == '':  # a separate line
                new_position = True
            elif new_position is True:  # position header
                cnt = 0
                category = chr(ord(category) + 1)
                new_position = False
                cur_position = name
                namelist_dict[cur_position] = []
            else:  # editors' names
                cnt += 1
                args = name.split()

                # split TG tag 
                if args[0].find('-@') != -1:
                    name_without_tag, tag_name = args[0].split('-@')
                    tag_list.append('@' + tag_name)
                    args[0] = name_without_tag

                namelist_dict[cur_position].append(' '.join(args))
        return namelist_dict, tag_list

    namelist_dict, tag_list = parse_namelist(namelist_orig)

    # Name list checking
    for position in namelist_dict:
        namelist = namelist_dict[position]
        partlist_str = bot_funct.checkPartlist(namelist, context.user_data['videolen'])
        if partlist_str != 'Good':
            update.message.reply_text('[/divpart]: @' + user + ' ' + partlist_str, quote=False)
            return

    partlist_full_str = title + '\n==========\n'

    for position in namelist_dict:
        namelist = namelist_dict[position]
        total_people = len(namelist)

        # check if video have srt
        if 'srt' not in context.user_data:
            partlist_str = genPartlist_str(user, context.user_data['videolen'], namelist, haveSrt=False, title=title)
            partlist_full_str += position + ' (0/{})\n'.format(total_people) + partlist_str + '\n'
        else:
            srt = context.user_data['srt']

            # print the list of parts
            editorList = genPartlist(context.user_data['videolen'], namelist.copy())

            # fillin srt start and end number to editorlist
            editorList = assignToSrt(srt, editorList)

            partlist_str = genPartlist_str(user, context.user_data['videolen'], namelist, haveSrt=True, editorList=editorList, title=title)
            partlist_full_str += position + ' (0/{})\n'.format(total_people) + partlist_str + '\n'

            if ('trans' in position or '翻譯' in position):
                # set up for File I/O
                file_title = editFileTitle(title)
                srtOutFile = open(file_title + '.srt', 'w', encoding='utf8')  # opens the file in write mode
                srtWithNameOutFile = open(file_title + '.txt', 'w', encoding='utf8')  # opens the file in write mode

                genSrtFile(srt, editorList, srtOutFile, srtWithNameOutFile)

                srtOutFile.close()
                srtWithNameOutFile.close()

                # send document to chat room
                update.message.reply_document(open(file_title + '.txt', 'rb'), quote=False)
                print(file_title + '.srt and ' + file_title + '.txt sent')

                # Delete file after sending it
                if os.path.exists(file_title + '.srt'):
                    os.remove(file_title + '.srt')
                if os.path.exists(file_title + '.txt'):
                    os.remove(file_title + '.txt')

        # initalize partlist_dict for current positon
        partlist_dict[position] = {
            "done_count" : 0,
            "total_count" : total_people, 
            "part" : []
        }

        # add editor into partlist_dict
        part_editor = ""
        part_time = ""
        for line_no in range(len(partlist_str.splitlines())):
            if line_no%2 == 1: 
                part_time = partlist_str.splitlines()[line_no]
                part = {
                    "editor" : part_editor, 
                    "time" : part_time, 
                    "ticks" : 0
                }
                partlist_dict[position]["part"].append(part)

            else: 
                part_editor = partlist_str.splitlines()[line_no]
            
    update.message.delete()
    bot_funct.DeleteConversationMessage(context.user_data['current_conversation_message'])
    print('Split part finished')

    update_latest = update.message.reply_text(partlist_full_str, quote=False)
    update_latest.pin()

    if chat_id != db.tg_chat_id['itTeamChatId'] and update_latest.chat.type != "private":
        # add new job to progresslist
        if title not in db.progresslist:
            db.progresslist[title] = []

        db.progresslist[title].append({
            "chat_id" : update_latest.chat_id, 
            "message_id" : update_latest.message_id, 
            "namelist" : partlist_dict
        })

        fileio.writeJson("progress.json", db.progresslist)
        bot_funct.show_progress(update, context)

    # tag editors
    tags = ' '.join(tag_list)
    tag_str = tags + '\n' + db.reply_msg_json[db.bot_mode]['startWorkingReminder']
    update.message = update_latest
    update.message.reply_text(tag_str, quote=True)

    # schedule a single reminder 
    if config.botName == config.publishBotName: 
        print('reminder for {} has been scheduled, reminder will be posted after 1.5 days, tags: {}'.format(title, tags))
        job = schedule_msg(update, context, time=1.5*24*60*60, msg=tags + '\n' + db.reply_msg_json[db.bot_mode]['reminderMessage'], target_id=chat_id, message_id = update_latest.message_id)
        context.chat_data[title] = job

    context.user_data.clear()
    return main.ConversationHandler.END


# generate the partlist
def genPartlist(duration, namelist):
    editorList = []
    total_time = int(duration)
    total_people = len(namelist)

    # handle preserved editors
    preserved_namelist = list()
    preserved_timelist = list()
    for i in range(len(namelist)):
        if len(namelist[i].split()) == 2:
            preserved_namelist.append(namelist[i].split()[0])
            preserved_timelist.append(int(float(namelist[i].split()[1]) * 60))
            namelist[i] = namelist[i].split()[0]

    # divide part by time
    if total_people - len(preserved_namelist) != 0:
        time_part = (total_time - sum(preserved_timelist)) // (total_people - len(preserved_namelist))
        diff = time_part % 5
        if diff > 3:
            time_part += 5 - diff
        else:
            time_part -= diff
        if time_part * (total_people - len(preserved_namelist)) > duration and time_part >= 10:
            time_part -= 5
    else:
        time_part = 0

    # fillin editorList
    preserved_index = 0
    splited_part = 0
    if total_people > 1:
        for i in range(total_people - 1):
            if namelist[i] in preserved_namelist:  # perserved
                editorList.append({'name': namelist[i],
                                   'duration': preserved_timelist[preserved_index],
                                   'partStart': splited_part,
                                   'partEnd': splited_part + preserved_timelist[preserved_index],
                                   'srtStart': 1,
                                   'srtEnd': 1})
                splited_part += preserved_timelist[preserved_index]
                preserved_index += 1
            else:  # normal assign
                editorList.append({'name': namelist[i],
                                   'duration': time_part,
                                   'partStart': splited_part,
                                   'partEnd': splited_part + time_part,
                                   'srtStart': 1,
                                   'srtEnd': 1})
                splited_part += time_part

    # part of the last people
    editorList.append({'name': namelist[total_people - 1],
                       'duration': total_time - splited_part,
                       'partStart': splited_part,
                       'partEnd': total_time,
                       'srtStart': 1,
                       'srtEnd': 1})
    return editorList


def genPartlist_str(user, duration, namelist, haveSrt, editorList='', title=''):
    total_time = int(duration)

    # handle preserved editors
    preserved_namelist = list()
    preserved_timelist = list()
    for i in range(len(namelist)):
        if len(namelist[i].split()) == 2:
            preserved_namelist.append(namelist[i].split()[0])
            preserved_timelist.append(int(float(namelist[i].split()[1]) * 60))
            namelist[i] = namelist[i].split()[0]

    # divide part by time
    total_people = len(namelist)
    if total_people - len(preserved_namelist) != 0:
        time_part = (total_time - sum(preserved_timelist)) // (total_people - len(preserved_namelist))
        diff = time_part % 5
        if diff > 3:
            time_part += 5 - diff
        else:
            time_part -= diff
        if time_part * (total_people - len(preserved_namelist)) > duration and time_part >= 10:
            time_part -= 5
    else:
        time_part = 0

    # put part to the output string
    preserved_index = 0
    splited_part = 0
    splitpart_str = ''
    end_text = ''
    for i in range(total_people):
        if i == total_people - 1:
            time_part = total_time - splited_part
            if namelist[i] in preserved_namelist:
                preserved_timelist[preserved_index] = time_part
            end_text = '(end)'
        else:
            end_text = ''
        if haveSrt:
            editorInfo = editorList[i]
            if namelist[i] in preserved_namelist:  # preserved
                splitpart_str += '{}\n>> {} ~ {}{} Sub No.{} ~ {}{}\n'.format(editorInfo['name'], sectotime(editorInfo['partStart']), sectotime(editorInfo['partEnd']), end_text, editorInfo['srtStart'], editorInfo['srtEnd'], end_text)
                splited_part += preserved_timelist[preserved_index]
                preserved_index += 1
            else:  # normal assign
                splitpart_str += '{}\n>> {} ~ {}{} Sub No.{} ~ {}{}\n'.format(editorInfo['name'], sectotime(editorInfo['partStart']), sectotime(editorInfo['partEnd']), end_text, editorInfo['srtStart'], editorInfo['srtEnd'], end_text)
                splited_part += time_part
        else:
            if namelist[i] in preserved_namelist:  # preserved
                splitpart_str += '{}\n>> {} ~ {}{}\n'.format(namelist[i], sectotime(splited_part), sectotime(splited_part + preserved_timelist[preserved_index]), end_text)
                splited_part += preserved_timelist[preserved_index]
                preserved_index += 1
            else:  # normal assign
                splitpart_str += '{}\n>> {} ~ {}{}\n'.format(namelist[i], sectotime(splited_part), sectotime(splited_part + time_part), end_text)
                splited_part += time_part
    return splitpart_str


# fillin srt start and end number to editorlist
def assignToSrt(srt, editorList):
    editorID = 0
    for sub in srt:
        editorInfo = editorList[editorID]
        subID = sub['subID']
        subStartTime = sub['start']
        editorStartTime = editorInfo['partStart']
        editorEndTime = editorInfo['partEnd']

        if (editorStartTime <= subStartTime and subStartTime <= editorEndTime):
            editorInfo['srtEnd'] = subID
        else:
            if editorID + 1 < len(editorList):
                editorID += 1
                editorInfo = editorList[editorID]
                editorInfo['srtStart'] = subID
    return editorList


# generate srt file
def genSrtFile(srt, editorList, srtOutFile, srtWithNameOutFile):
    editorID = 0

    # the first header
    editorInfo = editorList[editorID]
    printEditorName(srtWithNameOutFile, editorInfo)

    for sub in srt:
        # sub info
        subStartTime = sub['start']

        # editor info
        editorStartTime = editorInfo['partStart']
        editorEndTime = editorInfo['partEnd']

        # output to srt_output.srt
        printSub(srtOutFile, sub)

        # output to srt_with_name_output.srt
        # add header for each editor
        if (not(editorStartTime <= subStartTime and subStartTime <= editorEndTime)):
            if editorID + 1 < len(editorList):
                editorID += 1
                editorInfo = editorList[editorID]
                printEditorName(srtWithNameOutFile, editorInfo)

        printSub(srtWithNameOutFile, sub)


def printEditorName(file, editorInfo):
    (startHrs, startMin, startSec, startMilis) = timeFormat(editorInfo['partStart'])
    (endHrs, endMin, endSec, endMilis) = timeFormat(editorInfo['partEnd'])
    file.write('%s\n' % editorInfo['name'])
    file.write('>> %02d:%02d~%02d:%02d subNo. %d~%d\n' % (startMin, startSec, endMin, endSec, editorInfo['srtStart'], editorInfo['srtEnd']))


def printSub(file, sub):
    subID = sub['subID']
    subStartTime = sub['start']
    subEndTime = sub['end']
    engSub = sub['text']

    (startHrs, startMin, startSec, startMilis) = timeFormat(subStartTime)
    (endHrs, endMin, endSec, endMilis) = timeFormat(subEndTime)

    file.write('%d\n' % subID)
    file.write('%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n' % (startHrs, startMin, startSec, startMilis, endHrs, endMin, endSec, endMilis))
    file.write('%s\n\n' % engSub)


def editFileTitle(title):
    not_allowed_char = ['\\', '/', '*', ':', '?', '"', '<', '>', '|']
    
    for char in not_allowed_char:
        if char in title:
            title = title.replace(char, '')
    
    if len(title) == 0:
        title = 'empty_title'
    elif len(title) > 40:
        return title[:40]
    else:
        return title

# schedule a message with timer
def schedule_msg(update: Update, context: CallbackContext, time, msg, target_id, message_id):
    # context.bot.send_message(chat_id=target_id, text='Setting a timer for %d s!' % time)

    job_context = {'chat_id' : target_id, 
                    'message_id' : message_id,
                    'text' : msg}
    return context.job_queue.run_once(sendScheduledMsg, time, context=job_context)

def sendScheduledMsg(context: CallbackContext):
    job_context = context.job.context
    context.bot.send_message(chat_id=job_context['chat_id'], text=job_context['text'], reply_to_message_id=job_context['message_id'])
