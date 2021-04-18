import requests
from IPython.core.display import display, HTML# An API Error Exception

from bs4 import BeautifulSoup

entities = []
with open("20180730.txt") as file:
    lines = file.readlines()
    for line in lines:
        ent = line.split(" ")[0][1:-1]
        if ent != "14541":
            entities.append(ent)

class APIError(Exception):
    def __init__(self, status):
        self.status = status
    def __str__(self):
        return "APIError: status={}".format(self.status)
      
def edl(query):
    # Base URL for Spotlight API
    base_url = "http://api.dbpedia-spotlight.org/en/annotate"# Parameters 
    # 'text' - text to be annotated 
    # 'confidence' -   confidence score for linking
    params = {"text": query, "confidence": 0.35}# Response content type
    headers = {'accept': 'text/html'}# GET Request
    res = requests.get(base_url, params=params, headers=headers)
    if res.status_code != 200:
        # Something went wrong
        raise APIError(res.status_code)# Display the result as HTML in Jupyter Notebook

    text = res.text
    position = text.find("<a href=")
    my_list = []
    while position != -1:
        text = text[position+9:]
        quoteEnd = text.find('\"')
        if quoteEnd != -1:
            my_list.append(text[0:quoteEnd].split("/")[-1])
            text = text[quoteEnd:]
            position = text.find("<a href=")
    print(my_list)

    result_list = []
    for entity in my_list:
        if entity in entities:
            result_list.append(entity)
    return HTML(res.text), result_list