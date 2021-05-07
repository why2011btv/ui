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
import random
import json
# init flask app and env variables
app = Flask(__name__)
host = os.getenv("HOST")
port = os.getenv("PORT")

myclient = pymongo.MongoClient("mongodb+srv://chris:555Project2021@cluster0.kphap.mongodb.net/SearchEngine?retryWrites=true&w=majority")
mydb = myclient["SearchEngine"]
mycol = mydb["indexes_final"]
documents = mydb['documentsFull']

stop_words = []
with open('stop_words_en.txt') as f:
    lines = f.readlines()
    for line in lines:
        stop_words.append(line[0:-1])

def query2dict(query):
    query_dict = {}
    tokens = query.split(" ")
    token_list = []

    for token in tokens:
        token = token.lower()
        if token not in stop_words:
            token_list.append(token)
        if token not in query_dict.keys():
            query_dict[token] = 1
        else:
            query_dict[token] += 1

    for i in range(len(tokens) - 1):
        bigram = tokens[i] + ' ' + tokens[i+1]
        token_list.append(bigram)
        if bigram not in query_dict.keys():
            query_dict[bigram] = 1
        else:
            query_dict[bigram] += 1

    return query_dict, token_list

def pagerank_getter(url_list):
    # ad hoc
    results = {}
    for x in documents.find({'url': {'$in': url_list}}):
        try:
            results[x['url']] = {'pagerank': x['pagerank']}
        except:
            results[x['url']] = {'pagerank': 0.0015}
            print("pagerank not found for: ", x['url'])
    return results

def info_getter(url_list):
    results = {}
    for x in documents.find({'url': {'$in': url_list}}):
        results[x['url']] = {"title": x['title'], "description": x['snippet']}
    return results

def find_relevant_doc(query, token_list):
    doc_list = []
    lexicon = {}
    URL_WTD = {}
    for reverse_index in mycol.find({'lemma': {'$in': token_list}}):
        lemma = reverse_index['lemma']
        print(lemma)
        lexicon[lemma] = {'IDF': reverse_index['IDF']}
        for doc in reverse_index['docList']:
            url = doc['docURL']
            doc_list.append(url)
            if url in URL_WTD.keys():
                URL_WTD[url][lemma] = [doc['WTD'], int(doc['inTitle'])]
            else:
                URL_WTD[url] = {lemma: [doc['WTD'], int(doc['inTitle'])]}           
    
    return doc_list, lexicon, URL_WTD

def sort(doc_list, query, token_list, lexicon, URL_WTD):
    def compute_score(docURL, query, pagerank):
        cosine_score = 0.0
        inTitle_score = 0.0
        for token in query.keys():
            if token in URL_WTD[docURL].keys():
                cosine_score += lexicon[token]['IDF'] * query[token] * URL_WTD[docURL][token][0]
                inTitle_score += URL_WTD[docURL][token][1]
        # Harmonic Mean
        Total_Score = 2*(cosine_score * pagerank) / (cosine_score + pagerank)
        #print("cosine_score", cosine_score)
        #print("pagerank", pagerank)
        return Total_Score + inTitle_score

    print("getting info")
    results = info_getter(doc_list)
    print("getting pagerank")
    pageranks = pagerank_getter(doc_list)
    unsorted_dict = {}
    print("start to compute")
    for i in results.keys():
        unsorted_dict[i] = compute_score(i, query, pageranks[i]['pagerank'])
    print("score computation finished")
    sorted_dict = {k: v for k, v in sorted(unsorted_dict.items(), key=lambda item: item[1], reverse = True)}
    sorted_results = []
    
    for url in sorted_dict:
        #print(url)
        sorted_results.append({"title": results[url]['title'],
        "description": results[url]['description'],
        "url": url
        })
    return sorted_results

@app.route("/", methods=['GET'])
def search():
    """
    URL : /
    Query engine to find a list of relevant URLs.
    Method : POST or GET (no query)
    Form data :
        - query : the search query
        - hits : the number of hits returned by query
        - start : the start of hits
    Return a template view with the list of relevant URLs.
    """

    # GET data
    query = request.args.get("query", None)
    start = request.args.get("start", 0, type=int)
    hits = request.args.get("hits", 10, type=int)
    if start < 0 or hits < 0 :
        return "Error, start or hits cannot be negative numbers"
    
    if query:
        start_time = time.time()

        edl_result, entityList, edl_found_n, dolores_n = edl(query)
        print("entityList", entityList)
        query_dict, token_list = query2dict(query)

        if bool(query_dict):
            doc_list, lexicon, URL_WTD = find_relevant_doc(query_dict, token_list)
            print("found relevant doc")
            print(len(doc_list))
            print(time.time() - start_time)
            results = sort(doc_list, query_dict, token_list, lexicon, URL_WTD)
            data = {
                    "total": len(results),
                    "results": results
            }
        else:
            data = {
                    "total": 0,
                    "results": []
            }

        i = int(start/hits)
        if int(data["total"]/hits) * hits == data["total"]:
            maxi = int(data["total"]/hits)
        else:
            maxi = 1 + int(data["total"]/hits)
        if i >= 6:
            left_range = i-5
            if i+5 < maxi:
                right_range = i+5
            else:
                right_range = maxi
        else:
            left_range = 0
            if maxi < 10:
                right_range = maxi
            else:
                right_range = 10
        range_pages = range(left_range, right_range)
        print("start")
        print(start)
        print("hits")
        print(hits)

        end_time = time.time()
        
        # show the list of matching results
        return render_template('spatial/index.html', query=query,
            #response_time=r.elapsed.total_seconds(),
            response_time=format(end_time-start_time, '.4f'),
            total=data["total"],
            hits=hits,
            start=start,
            range_pages=range_pages,
            results=data["results"][start:start+hits],
            page=i,
            maxpage=maxi-1,
            edl=edl_result,
            entityList=entityList,
            edl_found_n = edl_found_n,
            dolores_n=dolores_n
            )
        
    # return homepage (no query)
    return render_template('spatial/index.html')

@app.route("/reference", methods=['POST'])
def reference():
    """
    URL : /reference
    Request the referencing of a website.
    Method : POST
    Form data :
        - url : url to website
        - email : contact email
    Return homepage.
    """
    # POST data
    data = dict((key, request.form.get(key)) for key in request.form.keys())
    if not data.get("url", False) or not data.get("email", False) :
        return "Vous n'avez pas renseigné l'URL ou votre email."

    # query search engine
    try :
        r = requests.post('http://%s:%s/reference'%(host, port), data = {
            'url':data["url"],
            'email':data["email"]
        })
    except :
        return "Une erreur s'est produite, veuillez réessayer ultérieurement"

    return "Votre demande a bien été prise en compte et sera traitée dans les meilleurs délais."

# -- JINJA CUSTOM FILTERS -- #

@app.template_filter('truncate_title')
def truncate_title(title):
    """
    Truncate title to fit in result format.
    """
    return title if len(title) <= 70 else title[:70]+"..."

@app.template_filter('truncate_description')
def truncate_description(description):
    """
    Truncate description to fit in result format.
    """
    if len(description) <= 160 :
        return description

    cut_desc = ""
    character_counter = 0
    for i, letter in enumerate(description) :
        character_counter += 1
        if character_counter > 160 :
            if letter == ' ' :
                return cut_desc+"..."
            else :
                return cut_desc.rsplit(' ',1)[0]+"..."
        cut_desc += description[i]
    return cut_desc

@app.template_filter('truncate_url')
def truncate_url(url):
    """
    Truncate url to fit in result format.
    """
    url = parse.unquote(url)
    if len(url) <= 60 :
        return url
    url = url[:-1] if url.endswith("/") else url
    url = url.split("//",1)[1].split("/")
    url = "%s/.../%s"%(url[0],url[-1])
    return url[:60]+"..." if len(url) > 60 else url
