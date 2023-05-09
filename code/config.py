import db

# bot info
# https://api.telegram.org/bot{token}/getUpdates
testBotName = 'testBot'
publishBotName = 'publishBot'
botName = publishBotName  # please switch the bot before you test/publish
if botName == testBotName:
    db.dev_mode = True
else: 
    db.dev_mode = False
bot_username = '{your_bot_username}'
bot_token = '{your_bot_token}'

youtube_data_api_key = '{your_youtube_api_key}'
