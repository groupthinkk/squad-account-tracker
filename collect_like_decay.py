from instagram.client import InstagramAPI
from instagram.bind import InstagramAPIError
from pymongo import MongoClient
from collections import deque
import sys
import time
import io
import csv
import datetime as dt

API_Queue = deque()

client = MongoClient()
db = client['SQUAD']

def getNextApi():
    global API_Queue
    ret = API_Queue.popleft()
    #print ret
    #print API_Queue
    return ret

def add_API_key(client_id = None, client_secret = None, access_token = None):
    db['api_keys'].insert({
        'client_id': client_id,
        'client_secret': client_secret,
        'access_token': access_token         
    })

def init_API_queue():
    global API_Queue
    api_keys = db['api_keys'].find()
    for key in api_keys:
        if key['access_token']:
            api = InstagramAPI(access_token=key['access_token'])
        else:
            api = InstagramAPI(client_id=key['client_id'], client_secret=key['client_secret'])
        API_Queue.append(api)

def get_user_posts(user_id):
    while(1):
        try:
            print user_id
            ret = API_Queue[0].user_recent_media(user_id=user_id, count=10)
            break
        except InstagramAPIError as e:
            print e.status_code
            if (int(e.status_code) == 429):
                print "Switching API key"
                getNextApi()
                if (len(API_Queue) == 0):
                    print "Out of API keys"
                    sys.exit(1)
            if (int(e.status_code) == 400):
                print "User %s is private" % (user_id)
                return False
    return ret

def add_username(username):
    if db['like_account_list'].find_one({"username": username}) != None:
        return False
    while(1):
        try:
            datalist = API_Queue[0].user_search(username, 100)
            break
        except InstagramAPIError as e:
            if (int(e.status_code) == 429):
                #print API_Queue
                getNextApi()
                if (len(API_Queue) == 0):
                    sys.exit(0)
    for data in datalist:
        if data.username == username:
            if get_user_posts(str(data.id)) != False:
                db['like_account_list'].insert({'username': username,'user_id':str(data.id)})
                return True
            else:
                return False
    return False

def do_pull():
    account_list = db['like_account_list'].find()
    for account in account_list:
        print account['username']
        posts, next = get_user_posts(account['user_id'])
        if posts == False:
            continue
        data_list = []
        for post in posts:
            data = {
                'post_id': post.id,
                'likes': post.like_count,
                'comments':post.comment_count,
                'username': post.user.username,
                'user_id': post.user.id,
                'created_time': post.created_time,
                'time': dt.datetime.utcnow()
            }
            data_list.append(data)
        db['like_log'].insert(data_list)

def export_like_data(f):
    fieldnames = ['post_id', 'likes', 'comments', 'username', 'user_id', 'created_time', 'time']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    post_ids = db['like_log'].distinct('post_id')
    for post_id in post_ids:
        data = db['like_log'].find({'post_id':post_id}).sort('time',1)
        include = False
        for entry in data:
            if entry['time'] - entry['created_time'] < dt.timedelta(minutes=10):
                include = True
                break
        if include:
            data.rewind()
            for entry in data:
                writer.writerow(entry)

def write_data_to_file():
    f = open("like_data.csv", "w")
    export_like_data(f)
    f.close()

def write_data_to_server():
    output = io.BytesIO()
    export_like_data(output)
    return output.getvalue()

init_API_queue()

if __name__ == '__main__':
    if sys.argv[1] == '0':
        do_pull()
    elif sys.argv[1] == '1':
        write_data_to_file()
    elif sys.argv[1] == '2':
        add_username(sys.argv[2])
    elif sys.argv[1] == '3':
        client_id = raw_input("client_id: ")
        client_secret = raw_input("client_secret: ")
        access_token = raw_input("access_token: ")
        if access_token != "":
            add_API_key(access_token=access_token)
        else:
            add_API_key(client_id=client_id, client_secret=client_secret)


            
