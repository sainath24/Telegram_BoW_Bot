from flask import Flask, request
import telegram
from bot_files.cred import bot_token, bot_user_name,URL
import pymongo

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token = TOKEN)

client = pymongo.MongoClient("mongodb+srv://***REMOVED***")
db = client.QuizBot

app = Flask(__name__)

def registerLevel(tid,update, collection,reg_level):
    if reg_level == 1:
        fn = update.message.text.encode('utf-8').decode()

        collection.find_one_and_update({'tid':tid},
        {'$set':{'first_name':fn}})

        collection.find_one_and_update({'tid':tid},
        {'$set':{'reg_level':2}})
        message = "Next enter your last name"
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return

    elif reg_level == 2:
        ln = update.message.text.encode('utf-8').decode()

        collection.find_one_and_update({'tid':tid},
        {'$set':{'last_name':fn}})

        collection.find_one_and_update({'tid':tid},
        {'$set':{'reg_level':3}})
        message = "What interests you? Enter your interests seperated by a comma"
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return


    elif reg_level == 3:
        interests = update.message.text.encode('utf-8').decode()
        interests = interests.split(',')

        collection.find_one_and_update({'tid':tid},
        {'$set':{'interests':interests}})

        collection.find_one_and_update({'tid':tid},
        {'$set':{'reg_level':4}})
        message = "Alright, that's all I want to know about you. Enter /learn topic_name to learn about a topic or enter /quiz topic_name to answer a quiz on the same. Have fun learning!"
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return




def registerUser(update): 
    # TODO: check if user is regstered if not register user
    tid = str(update.message.from_user.id)
    collection = db.Users
    user = collection.find_one({'tid':tid})
    if user and user['reg_level'] == 4:
        message = "Hello there" + user['first_name'] + "! You're already registered and good to go! Search for a topic with /learn topic_name or if you want to take a quiz, just send /quiz topic_name."
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return

    elif user:
        registerLevel(tid,update,collection,user['reg_level'])
        return
    
    # TODO: register new user
    message = "Hello there! Lets get started. First I'd like to get to know you. Please enter your first name"
    newUser = {
        "tid":tid,
        "reg_level":1,
        "first_name":None,
        "last_name":None,
        "interests":None,
        "past_quizzes":None,
        "current_quiz":None
    }
    collection.insert_one(newUser)
    bot.sendMessage(chat_id=update.message.chat_id,text=message)
    return



@app.route('/{}'.format(TOKEN), methods = ['POST'])
def respond():
    Users = db.Users
    update = telegram.Update.de_json(request.get_json(force = True), bot)

    tid = str(update.message.from_user.id)
    user = Users.find_one({'tid':tid})

    if user!=None and user['reg_level'] != 4:
        registerUser(update)
        return 'ok'

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