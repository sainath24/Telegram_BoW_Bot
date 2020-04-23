from flask import Flask, request
import telegram
from bot_files.cred import bot_token, bot_user_name,URL
import pymongo
from pymongo import MongoClient

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token = TOKEN)

client = pymongo.MongoClient("mongodb+srv://***REMOVED***")
db = client.QuizBot

app = Flask(__name__)


def registerUser(update): 
    # TODO: check if user is regstered if not register user
    tid = update.message.from_user.id
    collection = db.Users
    user = collection.find_one({'tid':str(tid)})
    if user:
        message = "Hello there" + user['first_name'] + "! You're already registered and good to go! Search for a topic with /search topic_name or if you want to take a quiz, just do /quiz topic_name."
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return
    
    # TODO: register new user
    message = 'New User'
    bot.sendMessage(chat_id=update.message.chat_id,text=message)
    return



@app.route('/{}'.format(TOKEN), methods = ['POST'])
def respond():
    update = telegram.Update.de_json(request.get_json(force = True), bot)

    
    poll = update.poll
    if poll:
        vote = poll.options
        print('inside poll\n')
        if vote[poll.correct_option_id].voter_count == 1:
            bot.sendMessage(chat_id=id,text='Right Answer')
        else:
            bot.sendMessage(chat_id=id,text='Wrong Answer, Right answer is: ' + vote[poll.correct_option_id].text )
        return 'ok'

    chat_id = update.message.chat_id
    message_id = update.message.message_id

    msg = update.message.text.encode('utf-8').decode()
    if msg == '/start':
        registerUser(update)
        return 'ok'
    
    
    

    opt = [[telegram.InlineKeyboardButton('test',callback_data='0'),telegram.InlineKeyboardButton('hey',callback_data='1')],[telegram.InlineKeyboardButton('sai',callback_data='2'),telegram.InlineKeyboardButton('bye',callback_data='3')]]
    opt = telegram.InlineKeyboardMarkup(inline_keyboard=opt)
    bot.sendPoll(chat_id=chat_id,question='ur name?',options=['test','hey','sai','bye'],type=telegram.Poll.QUIZ,correct_option_id=3,reply_markup=opt)

    return 'ok'

@app.route('/wh',methods = ['GET'])
def set_wh():
    s = bot.setWebhook('{URL}{HOOK}'.format(URL = URL,HOOK =TOKEN))
    if s:
        return 'wh success'
    return 'wh failed'


if __name__ == "__main__":
    app.run(threaded = True)