import requests
from IPython.core.display import display, HTML# An API Error Exception

from bs4 import BeautifulSoup

entities = {}
ent_count = 0
entities2id = {}
with open("20180730.txt") as file:
    lines = file.readlines()
    for line in lines:
        ent = line.split(" ")[0][1:-1]
        if ent != "14541":
            entities[ent_count] = ent
            entities2id[ent] = ent_count
            ent_count += 1

import torch
import torch.nn as nn
import h5py
with h5py.File('20180729.hdf5','r') as fin:
    a = fin['embedding'][...]
ent_emb = a[0:14541,:]
cos = nn.CosineSimilarity(eps=1e-6)
def topk(input_id):
    cosine = {}
    for i in range(14541):
        input1 = torch.tensor(ent_emb[input_id]).view([1, 100])
        input2 = torch.tensor(ent_emb[i]).view([1, 100])
        cosine[i] = cos(input1, input2).item()
    reverse_cos = {k: v for k, v in sorted(cosine.items(), key=lambda item: item[1], reverse=True)}
    k = 0
    return_list = []
    for key, value in reverse_cos.items():
        if k > 0 and k < 6:
            return_list.append(key)
        k += 1
    my_list = []
    for k in return_list:
        my_list.append(entities[k])
    return my_list

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
    return_text = res.text
    text = res.text
    return_text = return_text.replace("http://dbpedia.org/resource/", "https://en.wikipedia.org/wiki/")

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
    edl_found_n = len(my_list)

    result_list = []
    for entity in my_list:
        if entity in entities2id.keys():
            result_dict = {}
            result_dict['entity'] = entity
            result_dict['top5'] = topk(entities2id[entity])
            result_list.append(result_dict)
    
    return HTML(return_text), result_list, edl_found_n, len(result_list)