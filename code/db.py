from datetime import datetime, date

authorlist = []
whitelist = []
cred_json = {}
reply_msg_json = {}
progresslist = {}
bot_mode = 'default'
bot_mode_last_update = date(2020, 12, 24)
dev_mode = True

# group chat id
tg_chat_id = []

# special symbol
unicodeTick = '\u2714'

# Define state
GET_VIDEO_LEN, GET_KEYWORDorURL, GET_NAMELIST, GET_RESPONSE, WAITING_SETTING, WAITING_ANNOUNCE, END_TASK = range(7)