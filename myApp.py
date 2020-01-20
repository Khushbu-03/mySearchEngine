from  flask import Flask, jsonify
import pymongo
from operator import itemgetter
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords, words
from Trie import Trie

import math

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('words')
stop_words = set(stopwords.words('english'))
stemmer = nltk.stem.PorterStemmer()
tokenizer = nltk.tokenize
english_words = words.words()

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mySearchEngine"]
mongo_pages = mydb["pages"]
mongo_keys = mydb["keys"]
mongo_words = mydb["words"]

word_list = mongo_words.find_one()['words']
filtered_words = [word for word in word_list if not word.isnumeric() and english_words]
app = Flask(__name__)


@app.route('/autoComplete/<query>')
def getAutoComplete(query):
    trie = Trie(filtered_words)
    word_suggestion = jsonify({'query':query, 'results': trie.suggestions(query)})
    return word_suggestion

@app.route('/searchPages/<searchQuery>')
def getWebPages(searchQuery):
    try:
        tokenized_words = word_tokenize(searchQuery.lower(), 'english', False)
        unstop_words = [word for word in tokenized_words if word not in stop_words]
        stemmed_words = [stemmer.stem(words) for words in unstop_words]
        total_pages = mongo_pages.find().count()
        print(stemmed_words)
        tfidf_list = []
        tf = mongo_keys.find_one({'_id': stemmed_words[0]})["stem_tf"]
        idf = math.log(total_pages / len(tf))

        pages = {}
        for item in tf:
            for k,v in item.items():
                pages[k] = v * idf

        for k,v in pages.items():
            v = 0.6*v + 0.4*mongo_pages.find_one({"_id":k})['pageRank']
        results = sorted(pages.items(), key=itemgetter(1), reverse=True)

        return jsonify({'query': unstop_words[0],"results":[x[0] for x in results]} )

    except:
        return  jsonify({"query": filtered_words[0], "results": ""})
    return app