from flask import Flask, request
import telegram
from bot_files.cred import bot_token, bot_user_name,URL
import pymongo
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
import os

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
        "search":[],
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
        'applied science':'applied-science',
        'mathematics' : 'mathematics',
        'arts and humanities' : 'arts-and-humanities',
        'business and communication':'business-and-communication',
        'education' : 'education',
        'history' : 'history',
        'law' : 'law',
        'physical science' : 'physical-science'
    }

    edulevel = {
        'preschool' : 'preschool',
        'lower primary' : 'lower-primary',
        'upper primary':'upper-primary',
        'middle school':'middle-school',
        'high school':'high-school',
        'college':'college-upper-division'
    }

    url = 'https://www.oercommons.org/search?f.search=' + search[0].replace(' ', '+') + '&f.general_subject=' + subject[search[1]] + '&f.sublevel=' + edulevel[search[2]] + '&f.material_types=textbook&f.media_formats=downloadable-docs'
    print(url)
    rs = []
    page = requests.get(url)

    soup = BeautifulSoup(page.text,'html.parser')
    div = soup.findAll('div',{'class':'item-title'})

    count = 0 #get 5 courses
    for res in div:
        rurl = res.find('a',{'class':'item-link js-item-link'}).get('href')
        if '/courses/' in rurl and count<5:
            count+=1
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
        message = 'Enter the subject of the topic from one of the following:\nApplied Science\nArts and Humanities\nBusiness and Communication\nEducation\nHistory\nLaw\nMathematics\nPhysical Science\n Reply with /learn subject_name'
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
        search.append(topic)
        Users.find_one_and_update({'tid':user['tid']},
        {'$set':{'search':search}})
        rs = searchResource(update,user,Users)
        print(rs)
        message = 'Here are some resources,\n'
        for obj in rs:
            print(obj)
            message = message + obj['title'] + ' - ' + obj['link'] + '\n\n'

        bot.sendMessage(chat_id=update.message.chat_id, text=message)
        return
    # bot.sendMessage(chat_id=update.message.chat_id, text='This will fetch resources for topic ' + topic + ' and will keep a quiz ready')
    return

def genQuiz(update,topic,user,Users):


    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    topic = topic.replace(' ','%20')
    print('https://www.goconqr.com/en-US/search?q=' + topic + '%20quiz')
    driver.get('https://www.goconqr.com/en-US/search?q=' + topic + '%20quiz')
    driver.implicitly_wait(20)


    page = driver.page_source
    soup = BeautifulSoup(page,'html.parser')

    div = soup.findAll('a',{'class':'resource-tile__link'})
    # div = soup.findAll('div',{'class':'resource-tile__content'})
    print('links: ' + str(div))
    title_divs = soup.findAll('div',{'class':'resource-tile__title'})
    rs = []
    qcount = 0
    count = 0 #get 5 courses
    while count<5 and qcount<len(title_divs):
        if 'quiz' in title_divs[qcount].contents[0] or 'Quiz' in title_divs[qcount].contents[0] or 'QUIZ' in title_divs[qcount].contents[0]:
            rurl = div[qcount].get('href')
            count+=1
            addition = {}
            addition['title'] = title_divs[qcount].contents[0] #Title
            u = 'https://www.goconqr.com/en-US' + rurl #Link to quiz on goconqr
            addition['link'] = u
            rs.append(addition)
        qcount+=1
    # for res in div:
    #     if count<5 and ('quiz' in title_divs[count].contents[0] or 'Quiz' in title_divs[count].contents[0] or 'QUIZ' in title_divs[count].contents[0]):
    #         rurl = res.find('a',{'class':'resource-tile__link'}).get('href')
    #         count+=1
    #         addition = {}
    #         addition['title'] = title_divs[count-1].contents[0] #Title
    #         u = 'https://www.goconqr.com/en-US' + rurl #Link to quiz on goconqr
    #         addition['link'] = u
    #         rs.append(addition)
    
    message = 'Here are some quizzes you can try,\n'
    for obj in rs:
        print(obj)
        message = message + obj['title'] + ' - ' + obj['link'] + '\n\n'

    bot.sendMessage(chat_id=update.message.chat_id, text=message)
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
        # genQuiz(update,msg[7:],user,Users)
        return 'ok'

    elif len(msg) > 5 and msg[0:5] == '/quiz':
        genQuiz(update,msg[6:],user,Users)
        # getQuiz(update,msg[6:])
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


@app.route('/testsel',methods = ['GET','POST']) #test selenium
def seltest():
    # GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google_chrome'
    # CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
    # dic = request.get_json(force=True)
    # print(dic)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    # search = dic['search'].replace(' ','%20')
    # print('https://www.goconqr.com/en-US/search?q=' + search + '%20quiz')
    driver.implicitly_wait(20)
    driver.get('https://www.goconqr.com/en-US/search?q=calculus+quiz')
    element = driver.find_element_by_class_name("resource-tile__content")
    


    page = driver.page_source
    soup = BeautifulSoup(page,'html.parser')

    div = soup.findAll('div',{'class':'resource-tile__content'})
    # print(div)
    title_divs = soup.findAll('div',{'class':'resource-tile__title'})
    rs = []
    count = 0 #get 5 courses
    for res in div:
        if count<5 and 'quiz' in title_divs[count].contents[0] or 'Quiz' in title_divs[count].contents[0] or 'QUIZ' in title_divs[count].contents[0]:
            rurl = res.find('a',{'class':'resource-tile__link'}).get('href')
            count+=1
            addition = {}
            addition['title'] = title_divs[count-1].contents[0] #Title
            u = 'https://www.goconqr.com/en-US' + rurl #Link to quiz on goconqr
            addition['link'] = u
            rs.append(addition)

    print(rs)

    return str(page)


if __name__ == "__main__":
    app.run(threaded = True)


#  id(primary_key),website url, subject, level(beginner, intermediate, expert),    keyword

# user_id, level