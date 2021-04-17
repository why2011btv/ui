import requests
from IPython.core.display import display, HTML# An API Error Exception

from bs4 import BeautifulSoup


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
    
    return HTML(res.text)