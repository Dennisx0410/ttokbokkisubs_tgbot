# ttokbokkisubs_bot
# created by @ccn_juice and @TL_YenaDuck

version = '{version_code}'
toolName = 'ttokbokkisubs_bot v%s' % version
authorMsg = 'created by @ccn_juice and @TL_YenaDuck'
lastUpdate = '{last_update}'

# libraries
import os
import sys
import logging

# tg libraries
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
import config
import fileio
import functions as bot_funct
import divpart, done_job, doc, title, edit, delete, banner, announce, setting, new_job, reg_part, close_job
import db

# logging 
def logging():
    logging.basicConfig(format='Log: %(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

  
def setup_data():
    # read credential
    db.cred_json = fileio.readJson('credential.json')

    # read reply messsages
    basepath = 'reply_messages'
    with os.scandir(basepath) as entries:
        for entry in entries:
            if entry.is_file():
                path = os.path.join(basepath, entry.name)
                db.reply_msg_json[entry.name[0:-5]] = fileio.readJson(path)    

    bot_mode = 'default'

    # set up credential
    db.authorlist = db.cred_json['authorlist']
    db.whitelist = db.cred_json['whitelist']
    db.tg_chat_id = db.cred_json['chat_id']
    config.bot_username = db.cred_json['bots'][config.botName]['id']
    config.bot_token = db.cred_json['bots'][config.botName]['token']
    config.youtube_data_api_key = db.cred_json['youtube_data_api_key']

    # dev mode will change all chat id to IT team
    if db.dev_mode == True:
        for chatroom in db.tg_chat_id:
            if chatroom != 'pantryChatId':
                if 'test_' + chatroom in db.tg_chat_id:
                    db.tg_chat_id[chatroom] = db.tg_chat_id['test_' + chatroom]
                else:
                    db.tg_chat_id[chatroom] = db.tg_chat_id['itTeamChatId']
    if config.bot_token == '{your_bot_token}' or config.youtube_data_api_key == '{your_youtube_api_key}':
        print('Please edit {your_bot_token} and {your_youtube_api_key}!')
        sys.exit()


def setup_handler(dp, jq):
    newjob_handler = ConversationHandler(
        entry_points=[CommandHandler('newjob', new_job.start_newjob, filters=~Filters.update.edited_message)],
        states={
            db.GET_RESPONSE: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, bot_funct.getVidName),
                CommandHandler('newjob', bot_funct.multipleCommandMessage, filters=~Filters.update.edited_message)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.all, bot_funct.timeout),
            ]
        },
        fallbacks=[CommandHandler('cancel', bot_funct.cancel, filters=~Filters.update.edited_message)],
        name='newjob',
        conversation_timeout=180,
    )
    divpart_handler = ConversationHandler(
        entry_points=[CommandHandler('divpart', divpart.start_divpart, filters=~Filters.update.edited_message)],
        states={
            db.GET_KEYWORDorURL: [
                MessageHandler(Filters.regex('^[0-5][0-9]:[0-5][0-9]$') & ~Filters.update.edited_message, divpart.getVidLen),
                MessageHandler(Filters.text & ~(Filters.regex('^[0-5][0-9]:[0-5][0-9]$') | Filters.command) & ~Filters.update.edited_message, divpart.getKeywordOrURL),
                CommandHandler('divpart', bot_funct.multipleCommandMessage, filters=~Filters.update.edited_message)
            ],
            db.GET_NAMELIST: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, divpart.getNamelistnSplitTime),
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.all, bot_funct.timeout),
            ]
        },
        fallbacks=[CommandHandler('cancel', bot_funct.cancel, filters=~Filters.update.edited_message)],
        name='divpart',
        conversation_timeout=180,
    )
    banner_handler = ConversationHandler(
        entry_points=[CommandHandler('banner', banner.start_banner, filters=~Filters.update.edited_message)],
        states={
            db.GET_RESPONSE: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, bot_funct.getVidName),
                CommandHandler('banner', bot_funct.multipleCommandMessage, filters=~Filters.update.edited_message)
            ],
            db.GET_NAMELIST: [
                MessageHandler(Filters.text & ~Filters.command & ~Filters.update.edited_message, banner.getNameListnMakeBanner),
                CommandHandler('banner', bot_funct.multipleCommandMessage, filters=~Filters.update.edited_message)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.all, bot_funct.timeout),
            ]
        },
        fallbacks=[CommandHandler('cancel', bot_funct.cancel, filters=~Filters.update.edited_message)],
        name='banner',
        conversation_timeout=180,
    )
    announce_handler = ConversationHandler(
        entry_points=[CommandHandler('announce', announce.start_announce, filters=~Filters.update.edited_message)],
        states={
            db.WAITING_ANNOUNCE: [
                CallbackQueryHandler(announce.button_announce)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.all, bot_funct.timeout),
            ]
        },
        fallbacks=[CommandHandler('cancel', bot_funct.cancel, filters=~Filters.update.edited_message)],
        name='announce',
        conversation_timeout=20,
    )
    setting_handler = ConversationHandler(
        entry_points=[CommandHandler('setting', setting.start_setting, filters=~Filters.update.edited_message)],
        states={
            db.WAITING_SETTING: [
                CallbackQueryHandler(setting.button_setting)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.all, bot_funct.timeout),
            ]
        },
        fallbacks=[CommandHandler('cancel', bot_funct.cancel, filters=~Filters.update.edited_message)],
        name='setting',
        conversation_timeout=20,
    )
    closejob_handler = ConversationHandler(
        entry_points=[CommandHandler('closejob', close_job.start_closejob, filters=~Filters.update.edited_message)],
        states={
            db.WAITING_SETTING: [
                CallbackQueryHandler(close_job.button_closejob)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(Filters.all, bot_funct.timeout),
            ]
        },
        fallbacks=[CommandHandler('cancel', bot_funct.cancel, filters=~Filters.update.edited_message)],
        name='setting',
        conversation_timeout=20,
    )

    dp.add_handler(MessageHandler(filters=Filters.status_update.new_chat_members, callback=bot_funct.welcome))
    dp.add_handler(CommandHandler('info', bot_funct.info, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('updatenote', bot_funct.updatenote, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('help', bot_funct.helpmenu, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('done', done_job.done_job, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('undone', done_job.undone_job, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('doc', doc.add_doc, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('title', title.add_title, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('delete', delete.delete_msg, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('edit', edit.edit_msg, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('reg', reg_part.reg_part, filters=~Filters.update.edited_message))
    dp.add_handler(announce_handler)
    dp.add_handler(setting_handler)
    dp.add_handler(newjob_handler)
    dp.add_handler(closejob_handler)
    dp.add_handler(divpart_handler)
    dp.add_handler(banner_handler)
    dp.add_handler(CommandHandler('cancel', bot_funct.cancel, filters=~Filters.update.edited_message))
    dp.add_handler(CommandHandler('kill', bot_funct.kill, filters=Filters.user(username=db.authorlist) & ~Filters.update.edited_message))
    

def main():

    setup_data()

    # start bot
    print('Started ' + config.botName)
    
    updater = Updater(config.bot_token, use_context=True)
    dp = updater.dispatcher
    jq = updater.job_queue

    setup_handler(dp, jq)
    # updater.start_polling(drop_pending_updates=True)
    updater.start_webhook(listen='0.0.0.0',
                      port=8443,
                      url_path=db.cred_json['bots'][config.botName]['token'],
                      key='private.key',
                      cert='cert.pem',
                      webhook_url=f"https://{db.cred_json['bot_ip']}:8443/{db.cred_json['bots'][config.botName]['token']}")
    updater.idle()

    print('bot terminated')
