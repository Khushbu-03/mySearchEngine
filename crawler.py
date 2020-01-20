from bs4 import BeautifulSoup, Comment
import traceback
import requests
import urllib
from nltk.corpus import stopwords
from nltk import  word_tokenize
import nltk
from pymongo.errors import DuplicateKeyError

import pymongo

nltk.download('punkt')
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
stemmer = nltk.stem.PorterStemmer()
tokenizer = nltk.tokenize
crawled_links = []
word_list = set()
total_links = ['http://www.uwindsor.ca/']


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mySearchEngine"]
mongo_pages = mydb["pages"]
mongo_keys = mydb["keys"]
mongo_words = mydb["words"]
#print(myclient.list_database_names())

def saveToDB(url,links, stem_freq):
    page = {"_id": url, "links": links, "pageRank": 1}
    pg = mongo_pages.insert_one(page)
    for key,value in stem_freq.items():
        try:
           mongo_keys.update_one({"_id":key}, {"$addToSet": { "stem_tf" : {url:value}}}, upsert=True)
        except DuplicateKeyError:
            print("Keys insert error")



def true_texts(element):
    blacklist = [
        '[document]', 'noscript', 'header', 'html', 'meta', 'script', 'head', 'input', 'title', 'head', 'style'
    ]
    if element.parent.name in blacklist:
        return False
    if isinstance(element, Comment):
        return False
    return True

def parser(url):
    global crawled_links
    global total_links
    global word_list

    print('Handling: ' + url)
    crawled_links.append(url)
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    headers = {
        'User-Agent': user_agent
    }
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print("Crawl Error " + url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        links = list(urllib.parse.urljoin(url, link.get('href')) for link in soup.find_all('a'))
        total_links += links
        visible_texts = list(filter(true_texts, soup.find_all(text=True)))
        text = u' '.join(t.strip() for t in visible_texts)
        tokenized_words = word_tokenize(text.lower(), 'english', False)
        unstop_words = [word for word in tokenized_words if word not in stop_words]
        stemmed_words = [stemmer.stem(words) for words in unstop_words]
        freq_dist = nltk.probability.FreqDist(stemmed_words)
        total_words = len(stemmed_words)
        term_frequemcy = {k:v/total_words for k,v in freq_dist.items()}
        word_list.update(unstop_words)
        print(len(total_links))
    saveToDB(url,links,term_frequemcy)


while total_links:
    link = total_links.pop(0)
    try:
        mongo_words.update_one({"_id": "wordlist"}, {"$addToSet": { "words" :{"$each": list(word_list)}}}, upsert=True)
        word_list.clear()
    except Exception:
        print("insert word error")
        print(traceback.format_exc())
    if link not in crawled_links and not link.endswith(".pdf"):
        try :
            parser(link)
        except Exception:
            print("Page parser error")
            print(traceback.format_exc())


