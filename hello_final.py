
import aiml 
import os
import requests,json
import smtplib
from twilio.rest import TwilioRestClient
import gmail
import thread
import TOKENS
import Tweets_cassandra
import wikipedia
from PyDictionary import PyDictionary



from flask import Flask, render_template, redirect, url_for, request
app = Flask(__name__)
kernel = aiml.Kernel()
Question = None
dictionary=PyDictionary()



@app.route('/')
def hello_world():
    if os.path.isfile("bot_brain.brn"):
        kernel.bootstrap(brainFile = "bot_brain.brn")
    else:
        kernel.bootstrap(learnFiles = "std-startup.xml", commands = "load aiml b")
        kernel.saveBrain("bot_brain.brn")

    return 'Hello World!'

# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    Botresponse = None
    if request.method == 'POST':
        Botresponse = daemonCaller(request.form['question'] )
    return render_template('OfficeBotHome.html', answer=Botresponse)


def check_inbox(user, pwd) : 
    g = gmail.login(user, pwd)
    emails  = g.inbox().mail()
    mails = []
    for email in emails : 
        email.fetch()
        mails.append(email)
    return mails
    
def send_email(user, pwd, recipient, subject, body):
    print user, pwd, recipient, subject, body
    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body
    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
    except:
        return 0
    return 1

def call(number,ACCOUNT_SID,AUTH_TOKEN) :
    try :  
        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        call = client.calls.create(
            to=number,
            from_="+19256218459",
            url="http://demo.twilio.com/welcome/voice/",
            method="GET",
            fallback_method="GET",
            status_callback_method="GET",
            record="false"
            )
        return 1
    except :
        return 0

def text(number,msg,ACCOUNT_SID,AUTH_TOKEN) :
    try :
        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)  
        client.messages.create(
            to=number, 
            from_="+19256218459",   
            body = msg,
            )
        return 1
    except :
        return 0


def daemonCaller(question):

    # kernel now ready for use
        message = question#raw_input("Enter your message to the bot: ")
        if message == "quit":
            exit()
        elif message == "save":
            kernel.saveBrain("bot_brain.brn")

        elif 'weather' in message.strip().lower().split()  :
            try:

                url = 'http://api.openweathermap.org/data/2.5/weather?q=boulder,co,USA&appid=83364ebafb88eff14f89615a7067812f' 
                bot_response = (requests.get(url).json())        
                ans ="The forcast for today's weather is "
                weather_desc = bot_response['weather'][0]['description']
                temp = ((float(bot_response['main']['temp']) - 273.15) * 9.0/5.0 )  + 32.0
                bot_response = ans+ weather_desc +" with a temperature of "+str(temp)+" fahrenheit."
            except:
                bot_response = "Cannot fetch weather data"
            return bot_response


        #Email
        elif message.lower().startswith('email') : 
            kernel.setBotPredicate("email",'pipa09799@gmail.com')
            kernel.setBotPredicate("pwd",'hackcu123')
            s = message
            receiver = s[s.find('@TO')+len('@TO'):s.find('@SUBJECT')].strip()
            subject = s[s.find('@SUBJECT')+len('@SUBJECT'):s.find('@BODY') ].strip()
            body = s[s.find('@BODY')+len('@BODY'): ].strip()
            bot_response = send_email(kernel.getBotPredicate("email"),kernel.getBotPredicate("pwd"), receiver, subject , body)
            if bot_response == 0:
                bot_response = "Email failed...."
            else:
                bot_response = "Email sent successful...."
            return bot_response
        #Inbox
        elif 'inbox' in message.strip().lower().split() :
            bot_response = ''
            kernel.setBotPredicate("email",'pipa09799@gmail.com')
            kernel.setBotPredicate("pwd",'hackcu123')
            emails = check_inbox(kernel.getBotPredicate("email"),kernel.getBotPredicate("pwd"))
            for email in emails :
               bot_response += 'Subject :  ' + email.subject + ' (' + email.fr + ') \n\n'
            return  bot_response
        
        #News       
        elif  'news' in message.strip().lower().split()  :
            url = 'http://content.guardianapis.com/search?api-key=test'
            bot_response = (requests.get(url).json())
            try:
                ans =" "
                bot_response = bot_response['response']["results"]
                for each in bot_response:
                    ans += each["webTitle"]+"\n"+each["webUrl"]+"\n\n"
                bot_response = ans
            except:
                bot_response =   "Cannot fetch news"
            return bot_response
            


        elif message.strip().lower().split()[0] == "wiki":
            bot_response = wikipedia.summary(message.strip().lower().split()[1:],sentences=2)
            return bot_response

        #tasks
        elif message.strip().split()[0].lower() == 'tasks' :
            bot_response = ''
            if len(message.strip().split()) == 1 :
                    bot_response = ','.join(kernel.getBotPredicate("tasks").split('#'))
            elif message.strip().split()[1].lower() == '@add' :
                    kernel.setBotPredicate("tasks", kernel.getBotPredicate("tasks") + '#' + message.strip().split('@add')[1].strip())
                    bot_response = 'Task Added...'
            elif message.strip().split()[1].lower() == '@clean' :
                    kernel.setBotPredicate('tasks' , '')
                    bot_response = 'Tasks Cleaned...'
            return bot_response

        elif message.lower().startswith('call'):
            bot_response = ''
            number = message.strip().split()[1]
            bot_response = call(number,"AC7c216d7ff5cfb6b095ae2717304e1e0a","dcfe32cff135a34964e76408c7e651fc")
            if (bot_response == 1):
                bot_response = "Call connecting ..."
            else:
                bot_response = "Cannot connect..."
            return bot_response


        elif message.strip().split()[0] == "tweet":
            flag = None
            tw = Tweets_cassandra.TweetAPI()
            try:
                flag = 0
                tw.postTweet(" ".join(message.strip().split()[1:]))
            except:
                flag = 1
            if (flag == 0 ):
                return  "Tweet successful"
            else:
                return "Tweet Failed"




        elif " ".join(message.strip().lower().split()[:2]) == "synonym of":
            bot_response =  dictionary.synonym(" ".join(message.strip().lower().split()[2:]))
            if(len(bot_response) >= 1 ):
                bot_response = ", ".join(bot_response)
            else:
                bot_response = "Sorry i couldn't find the synonym for "," ".join(bot_response)
            return bot_response

        elif " ".join(message.strip().lower().split()[:2]) == "antonym of":        
            bot_response =  (dictionary.antonym(" ".join(message.strip().lower().split()[2:])))
            if(len(bot_response) >= 1 ):
                bot_response = ", ".join(bot_response)
            else:
                bot_response = "Sorry i couldn't find the antonym for "," ".join(bot_response)
            return bot_response


        elif " ".join(message.strip().lower().split()[:2]) == "meaning of":
            bot_response =  dictionary.meaning(" ".join(message.strip().lower().split()[2:]))
            if len (bot_response.keys()) == 0  :
                bot_response = "Sorry, Couldn't find the meaning "
            else:
                if 'Noun' in bot_response.keys():
                    return bot_response['Noun'][0]
                else:
                    return "Not found"




            #print bot_response

        elif message.lower().startswith('text') :
            bot_response = ''
            s = message
            number = s[:s.find('@BODY') ].strip().split()[1]
            body = s[s.find('@BODY')+ len('@BODY'): ].strip()
            bot_response = text(number, body, "AC7c216d7ff5cfb6b095ae2717304e1e0a","dcfe32cff135a34964e76408c7e651fc")
            if (bot_response == 1):
                bot_response = "SMS sent"
            else:
                bot_response = "Sending SMS Failed "
            return bot_response

        #AIML   
        else:
            bot_response = kernel.respond(message)
            return bot_response
            # Do something with bot_response





if __name__ == '__main__':

	app.debug = True
	app.run()