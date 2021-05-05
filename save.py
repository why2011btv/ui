import os
import requests
from urllib import parse
from flask import Flask, request, jsonify, render_template
from edl import *
import pymongo
import bs4
import urllib.request
import time
import re
import json
# init flask app and env variables
app = Flask(__name__)
host = os.getenv("HOST")
port = os.getenv("PORT")

myclient = pymongo.MongoClient("mongodb+srv://chris:555Project2021@cluster0.kphap.mongodb.net/SearchEngine?retryWrites=true&w=majority")
mydb = myclient["SearchEngine"]
mycol = mydb["indexes_final"]
documents = mydb['documentsFull']
mydoc = mycol.find({'lemma' : { "$not": {"$regex" : ".* .*"} }})
lexicon = {}
URL_WTD = {}
num = 0

def pop_(list_a):
    for i in list_a:
        i.pop("docObjID")
    return list_a

start_time = time.time()
for x in mydoc:
    num += 1
    lexicon[x['lemma']] = {'IDF': x['IDF'], 'docList': pop_(x['docList'])}
    for doc in x['docList']:
        if doc['docURL'] in URL_WTD.keys():
            URL_WTD[doc['docURL']][x['lemma']] = doc['WTD']
        else:
            URL_WTD[doc['docURL']] = {x['lemma']: doc['WTD']}
    if num % 10000 == 0:
        print(num)
        print(x['lemma'])
    #if num == 2000:
    #    break
print(num)
end_time = time.time()    
print(end_time - start_time)
with open("lexicon.json", 'w') as f_l:
    json.dump(lexicon, f_l)

with open("URL_WTD.json", "w") as f_W:
    json.dump(URL_WTD, f_W)