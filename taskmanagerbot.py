import json 
import requests
import time
import urllib
from dbhelper import DBHelper
db = DBHelper()

#API token provided by telegram Botfather
TOKEN = "<API TOKEN HERE>"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100000"
    if offset:
      url +="&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


#used to get the last update's chat id and text from telegram API
def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

#for developer use:
def log(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    name = updates["result"][last_update]["message"]["chat"]["username"]
    return name

#to send message to users
def send_message(text, chat_id,reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    if reply_markup:
       url += "&reply_markup={}".format(reply_markup)
    get_url(url)
    

#to get the last update id from telegram API
def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)



#inline keyboard with add,remove,show,delete list
def build_kboard(options):
     keyboard = [[item] for item in options]
     reply_markup = {"keyboard":keyboard,"one_time_keyboard": True}
     return json.dumps(reply_markup)



#most important function that maintains the bot
def handle_updates(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            items = db.get_items(chat) ##
            options = ['add task', 'remove task', 'show tasks','delete list']
            kboard=build_kboard(options)
            if text == "delete list":
                for item in items:
                    db.delete_item(item,chat)
                send_message("No tasks remaining.",chat)
                send_message("Want to create a new list?",chat,kboard)

            
            elif text == "/start":
               send_message("Welcome to your personal TASK MANAGER. Send me your tasks and i'll remember.", chat)
               send_message("Add tasks",chat,kboard)
            
            elif text == "show tasks":
                 message = "\n".join(items)
                 message1 = "Your tasks are:\n" + message
                 send_message(message1,chat)
                 send_message("What to do want to do?",chat,kboard)

            elif text == 'remove task': 
                        if items:
                                keyboard = build_keyboard(items)
                                send_message("Select a task to delete",chat,keyboard)
                        else:
                                send_message("No tasks remaining! :)",chat)
 
            elif text[0] == '-':
                 task = text[2:]
                 db.delete_item(task,chat)
                 items = db.get_items(chat)
                 message = "\n".join(items)
                 message1 = "Your remaining tasks are:\n" + message
                 send_message(message1,chat)
                 send_message("What do you want to do?",chat,kboard)
            else:
               if text == 'add task':
                        send_message("send me a task",chat)
               elif text not in items:
                         db.add_item(text, chat) ##
                         items = db.get_items(chat) ##
                         message = "\n".join(items)
                         message1 = "Your current tasks are:\n" + message
                         send_message(message1, chat)
                         send_message("What do you want to do?",chat,kboard) 
               elif text in items:
                         send_message("Task already remaining",chat)
                         send_message("What do you want to do?",chat,kboard)
                                  
               
        except KeyError:
            pass



#inline keyboars used in removing a task
def build_keyboard(items):
    keyboard = [["- " + item] for item in items]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)



def main():
    db.setup()
    last_update_id = None
    while True:
        print('Getting updates...')
        updates = get_updates(last_update_id)
        log_name = log(updates)
        print("{} is messaging".format(log_name))
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)

if __name__ == '__main__':
	main()
