from flask import Flask, request
import telegram
from bot_files.cred import bot_token, bot_user_name,URL
import pymongo
from bs4 import BeautifulSoup
import requests

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token = TOKEN)

client = pymongo.MongoClient("mongodb+srv://***REMOVED***")
db = client.QuizBot

update_list = []

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
        {'$set':{'last_name':ln}})

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
    tid = str(update.message.from_user.id)
    collection = db.Users
    user = collection.find_one({'tid':tid})
    if user and user['reg_level'] == 4:
        message = "Hello there " + user['first_name'] + "! You're already registered and good to go! Search for a topic with /learn topic_name or if you want to take a quiz, just send /quiz topic_name."
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return

    elif user:
        registerLevel(tid,update,collection,user['reg_level'])
        return
    
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

def searchResource(update, user, Users):
    search = user['search']
    Users.find_one_and_update({'tid':user['tid']},
    {'$set':{'search':[]}})
    subject = {
        'Applied science':'applied-science',
        'Mathematics' : 'mathematics',
        'Arts and humanities' : 'arts-and-humanities',
        'Business and communication':'business-and-communication',
        'Education' : 'education',
        'History' : 'history',
        'Law' : 'law',
        'Physcial science' : 'physical-science'
    }

    edulevel = {
        'Preschool' : 'preschool',
        'Lower primary' : 'lower-primary',
        'Upper primary':'upper-primary',
        'Middle school':'middle-school',
        'High school':'high-school',
        'College':'college'
    }

    url = 'https://www.oercommons.org/search?f.search=' + search[0] + '&f.general_subject=' + search[1] + '&f.sublevel=' + search[2] + '&f.material_types=textbook&f.media_formats=downloadable-docs'
    rs = []
    page = requests.get(url)

    soup = BeautifulSoup(page.text,'html.parser')
    div = soup.findAll('div',{'class':'item-title'})

    for res in div:
        rurl = res.find('a',{'class':'item-link js-item-link'}).get('href')
        if '/courses/' in rurl:
            addition = {}
            addition['title'] = res.find('a',{'class':'item-link js-item-link'}).contents[0] #Title
            # print(rurl + '\n')
            u = rurl + '/view'  #Link to reource on oer
            # print(u)
            p = requests.get(u)
            s = BeautifulSoup(p.text,'html.parser')
            d = s.findAll('div',{'class':'modal-footer'})
            for r in d:
                try:
                    furl = r.find('a',{'class':'js-continue-redirect-button'}).get('href') #Link to actual reosource that will be sent to user
                    addition['link'] = furl
                    #  print(furl + '\n\n')
                    rs.append(addition)
                    break
                except:
                    continue

    return rs

    



def getResources(update,topic,user,Users):
    # TODO: get search resuts from ml algorithm and return results
    # genQuiz(topic) maybe in a parallel thread
    search = user['search']
    if search == None or len(search) == 0:
        search.append(topic)
        Users.find_one_and_update({'tid':user['tid']},
        {'$set':{'search':search}})
        message = 'Enter the subject of the topic from one of the following:Applied Science\nArts and Humanities\nBusiness and Communication\nEducation\nHistory\nLaw\nMathematics\nPhysical Science\n Reply with /learn subject_name'
        bot.sendMessage(chat_id=update.message.chat_id,text=message)
        return

    elif len(search) == 1:
        search.append(topic)
        Users.find_one_and_update({'tid':user['tid']},
        {'$set':{'search':search}})
        message = 'Enter Education level:\nPreschool\nLower Primary\nUpper Primary\nMiddle School\nHigh School\nCollege\nReply with /learn education_level'
        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return
    
    elif len(search) == 2:
        rs = searchResource(update,user,Users)
        message = 'Here are some resources,\n'
        for obj in rs:
            message += obj['title'] + ' - ' + obj['link'] + '\n'

        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return
    # bot.sendMessage(chat_id=update.message.chat_id, text='This will fetch resources for topic ' + topic + ' and will keep a quiz ready')
    return

def getQuiz(update,topic):
    # TODO: generate quiz with ml algo
    collection = db.Quizzes
    quiz = collection.find_one({'topic':topic})
    if quiz:
        questions = quiz['quiz']
        for question in questions:
            bot.sendPoll(chat_id=update.message.chat_id,question = question['question'],
            options=[question['op1'],question['op2'],question['op3'],question['op4']],
            type=telegram.Poll.QUIZ,
            correct_option_id=question['correct_op'])
        return
    message = 'Sorry, no quizzes found on topic '+ topic + '. Please try again later'
    bot.sendMessage(chat_id=update.message.chat_id, text=message)


@app.route('/{}'.format(TOKEN), methods = ['POST'])
def respond():
    Users = db.Users
    update = telegram.Update.de_json(request.get_json(force = True), bot)
    # if update!=None and update.update_id in update_list:
    #     return 'ok'

    update_list.append(update.update_id)

    if update.message == None:
        return 'ok'

    tid = str(update.message.from_user.id)
    user = Users.find_one({'tid':tid})

    # poll = update.poll
    # if poll:
    #     # vote = poll.options
    #     # print('inside poll\n')
    #     # if vote[poll.correct_option_id].voter_count == 1:
    #     #     bot.sendMessage(chat_id=id,text='Right Answer')
    #     # else:
    #     #     bot.sendMessage(chat_id=id,text='Wrong Answer, Right answer is: ' + vote[poll.correct_option_id].text )
    #     return 'ok'

    if user!=None and user['reg_level'] != 4:
        registerUser(update)
        return 'ok'

    chat_id = update.message.chat_id
    message_id = update.message.message_id

    msg = update.message.text.encode('utf-8').decode()
    if msg == '/start':
        registerUser(update)
        return 'ok'

    elif len(msg) > 6 and msg[0:6] == '/learn':
        getResources(update,msg[7:],user,Users)
        return 'ok'

    elif len(msg) > 5 and msg[0:5] == '/quiz':
        getQuiz(update,msg[6:])
        return 'ok'
    
    # opt = [[telegram.InlineKeyboardButton('test',callback_data='0'),telegram.InlineKeyboardButton('hey',callback_data='1')],[telegram.InlineKeyboardButton('sai',callback_data='2'),telegram.InlineKeyboardButton('bye',callback_data='3')]]
    # opt = telegram.InlineKeyboardMarkup(inline_keyboard=opt)
    # bot.sendPoll(chat_id=chat_id,question='ur name?',options=['test','hey','sai','bye'],type=telegram.Poll.QUIZ,correct_option_id=3,reply_markup=opt)
    return 'ok'

@app.route('/wh',methods = ['GET'])
def set_wh():
    s = bot.setWebhook('{URL}{HOOK}'.format(URL = URL,HOOK =TOKEN))
    if s:
        return 'wh success'
    return 'wh failed'


if __name__ == "__main__":
    app.run(threaded = True)


#  id(primary_key),website url, subject, level(beginner, intermediate, expert),    keyword

# user_id, level