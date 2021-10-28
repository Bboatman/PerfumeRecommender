import requests
from bs4 import BeautifulSoup
import nltk
import pickle
import os
import time
import json
script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path = "fragrances.p"
pickleFile = os.path.join(script_dir, rel_path)

seen = []
categoryUrls = [
"https://blackphoenixalchemylab.com/product-category/limited-edition/"
]

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

def getMasterList(url):
    url = "https://blackphoenixalchemylab.com/product-category/general-catalog-perfume-oils/"
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    res = soup.find_all("li", {"class": "product-category"}) 
    return [x["href"] for x in res]

def getCategoryScents(childUrl, seenScents):
    req = requests.get(childUrl, headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    res = soup.find_all("a", {"class": "woocommerce-loop-product__link"})
    productUrls = []
    for x in res:
        name = x.text
        url = x['href']
        if name not in seenScents:
            productUrls.append(url)
        
    return set(productUrls)

def getTextOfScent(childUrl):
    req = requests.get(childUrl, headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    name = soup.find_all("h1", {"class":"product_title"})[0].text
    bodyDivs = soup.find_all("div", {"class":"woocommerce-product-details__short-description"})
    tags = [x.find_all("a") for x in soup.find_all("span", {"class":"tagged_as"})]
    tagBody = []
    if (len(tags) > 0):
        tagBody = [x.text for x in tags[0]]
    body = [x.text for x in bodyDivs][0]
    return {"name": name, "body": body.lower(), "tags": tagBody}

def extractNouns(text):
    is_noun = lambda pos: pos[:2] == 'NN'
    tokenized = nltk.word_tokenize(text)
    nouns = list(set([word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos) and len(word) > 2]))
    return nouns

def buildModel():
    fragranceList = []
    try:
        fragranceList = pickle.load(open(pickleFile, "rb" ))
    except:
        pass

    fragranceNames = [x["name"] for x in fragranceList]
    print(len(fragranceNames))
    try:
        prevCount = len(fragranceNames)
        for category in categoryUrls:
            if category not in seen:
                seen.append(category)
                productUrls = list(getCategoryScents(category, fragranceNames))
                for product in productUrls:
                    scent = getTextOfScent(product)
                    if scent["name"] not in fragranceNames:
                        if "Perfume Oil" in scent["name"]:
                            scent["notes"] = extractNouns(scent["body"])
                            fragranceList.append(scent)
                            fragranceNames.append(scent["name"])

                            if len(fragranceNames) % 5 == 0 and len(fragranceNames) != prevCount:
                                print("Saving: " + scent["name"])
                                print("Found: " + str(len(fragranceNames)))
                                prevCount = len(fragranceNames)
                    time.sleep(5)


                print("Finished category: " + category)
    except Exception as inst:
        print(type(inst))    # the exception instance
        print(inst.args)     # arguments stored in .args
        print(inst)   
    
    pickle.dump(fragranceList, open(pickleFile, "wb" ))

def pickleToJSON():
    fragranceList = pickle.load(open(pickleFile, "rb" ))
    print(len(fragranceList))
    with open('data.txt', 'w') as outfile:
        json.dump(fragranceList, outfile)

buildModel()