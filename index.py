import os
import requests
from urllib import parse
from flask import Flask, request, jsonify, render_template
from edl import *
import pymongo

# init flask app and env variables
app = Flask(__name__)
host = os.getenv("HOST")
port = os.getenv("PORT")

myclient = pymongo.MongoClient("mongodb+srv://chris:555Project2021@cluster0.kphap.mongodb.net/SearchEngine?retryWrites=true&w=majority")
mydb = myclient["SearchEngine"]
mycol = mydb["indexes"]

mydoc = mycol.find().sort("lemma")
lexicon = {}
URL_WTD = {}

for x in mydoc:
    lexicon[x['lemma']] = {'IDF': x['IDF'], 'docList': x['docList']}
    for doc in x['docList']:
        if doc['docURL'] in URL_WTD.keys():
            URL_WTD[doc['docURL']][x['lemma']] = doc['WTD']
        else:
            URL_WTD[doc['docURL']] = {x['lemma']: doc['WTD']}

def find_relevant_doc(query):
    doc_list = []
    for token in query.keys():
        for doc in lexicon[token]['docList']:
            doc_list.append(doc['docURL'])
    return doc_list

def compute_score(docURL, query):
    score = 0.0
    for token in query.keys():
        if token in URL_WTD[docURL].keys():
            score += lexicon[token]['IDF'] * query[token] * URL_WTD[docURL][token]
    return score

def sort(doc_list, query):
    unsorted_dict = {}
    for docURL in doc_list:
        unsorted_dict[docURL] = compute_score(docURL, query)
    sorted_dict = {k: v for k, v in sorted(unsorted_dict.items(), key=lambda item: item[1], reverse = True)}
    results = []
    for url in sorted_dict:
        results.append({"title": "A title here",
        "description": "A description here",
        "url": url
        })
    return results

def query2dict(query):
    query_dict = {}
    tokens = query.split(" ")
    for token in tokens:
        if token not in lexicon.keys():
            return {'!': 1}
        else:
            if token not in query_dict.keys():
                query_dict[token] = 1
            else:
                query_dict[token] += 1
    return query_dict

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
    
    if query :
        query_dict = query2dict(query)
        results = sort(find_relevant_doc(query_dict), query_dict)

        data = {
                "total": 40,
                "results": results
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
        edl_result, entityList, edl_found_n, dolores_n = edl(query)
        print(entityList)
        # show the list of matching results
        return render_template('spatial/index.html', query=query,
            #response_time=r.elapsed.total_seconds(),
            response_time=0.01,
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
