from flask import Flask, request
import telegram
from bot_files.cred import bot_token, bot_user_name,URL

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token = TOKEN)

app = Flask(__name__)

@app.route('/{}'.format(TOKEN), methods = ['POST'])
def respond():
    update = telegram.Update.de_json(request.get_json(force = True), bot)

    chat_id = update.message.chat_id
    message_id = update.message.message_id
    # p = update.m
    # if p:
    #     bot.sendMessage(chat_id=chat_id,text= 'poll answered')
    #     return 'ok'

    # b1 = telegram.InlineKeyboardButton(text='test')
    # b2 = telegram.InlineKeyboardButton(text='hey')
    # b3 = telegram.InlineKeyboardButton(text='sai')
    # b4 = telegram.InlineKeyboardButton(text='bye')
    opt = [[telegram.InlineKeyboardButton(text='test') for _ in range(2)] for _ in range(2)]
    opt = telegram.InlineKeyboardMarkup(opt)
    # poll = telegram.Poll(id='1',question='ur name?',options=['test','hey','sai','bye'],type='QUIZ',correct_option_id=3)
    bot.sendPoll(chat_id=chat_id,question='ur name?',options=['test','hey','sai','bye'],type=telegram.Poll.QUIZ,correct_option_id=3,reply_markup=opt)
    # msg = update.message.text.encode('utf-8').decode()

    # bot.sendPoll(chat_id=chat_id,question='ur clg?',options=['test','hey','ssn','annuniv'],type=telegram.Poll.QUIZ,correct_option_id=2)
    

    # bot.sendMessage(chat_id = chat_id, text = msg,reply_to_message_id=message_id)

    return 'ok'

@app.route('/wh',methods = ['GET'])
def set_wh():
    s = bot.setWebhook('{URL}{HOOK}'.format(URL = URL,HOOK =TOKEN))
    if s:
        return 'wh success'
    return 'wh failed'


if __name__ == "__main__":
    app.run(threaded = True)