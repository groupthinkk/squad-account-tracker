#!/usr/bin/env python

from pymongo import MongoClient
import requests
import datetime as dt
import csv
import sys
import io

client = MongoClient()
db = client['SQUAD']

client_id='375701af44384b6da4230f343a528b92'
client_secret='9620d4aef36f4e5b9139731497babcdb'
access_token='2963667.375701a.3eae9d0208074293b2bfe5c0c917f1b1'


def add_username(username):
    if db['account_list'].find_one({"username": username}) != None:
        return False
    url = ('https://api.instagram.com/v1/users/search?q=%s&access_token=%s') % (username, access_token)
    j = requests.get(url)
    j = j.json()
    datalist = j['data']
    for data in datalist:
        if data['username'] == username:
            db['account_list'].insert({'username': username,'user_id':str(data['id'])})
            return True
    return False


def get_account_list():
    l = []
    raw_db = db['account_list'].find()
    for entry in raw_db:
        l.append([entry['username'], entry['user_id']])
    return l


def get_follower_count(username, user_id):
    url = ('https://api.instagram.com/v1/users/%s/?access_token=%s') % (user_id, access_token)
    r = requests.get(url).json()
    try:
        follow_count = r['data']['counts']['followed_by']
        entry = {
            "date": dt.datetime.today(),
            "username": username,
            "user_id": user_id,
            "follow_count": follow_count
        }
        db['account_data'].insert(entry)
    except:
        print username, r


def process_account_list(account_list):
    for account in account_list:
        get_follower_count(account[0], account[1])


def export_account_data():
    csvfile = open('account_data.csv', 'w')
    data = db['account_data'].find().sort([('username', 1), ('date', 1)])
    fieldnames = list(data[0].keys())
    fieldnames.remove("_id")
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for entry in data:
        del entry['_id']
        entry['date'] = entry['date'].date()
        writer.writerow(entry)
    csvfile.close()


def serve_account_data():
    output = io.BytesIO()
    data = db['account_data'].find().sort([('username', 1), ('date', 1)])
    fieldnames = list(data[0].keys())
    fieldnames.remove("_id")
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in data:
        del entry['_id']
        entry['date'] = entry['date'].date()
        writer.writerow(entry)
    return output.getvalue()


if __name__ == '__main__':
    if sys.argv[1] == '0':
        account_list = get_account_list()
        process_account_list(account_list)
        print "Account data pulled for: ", dt.date.today()
    elif sys.argv[1] == '1':
        export_account_data()
    elif sys.argv[1] == '2':
        add_username(sys.argv[2])
