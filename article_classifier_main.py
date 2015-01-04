import nltk
import random
import urllib
import lxml.html
import os
from bs4 import BeautifulSoup
import datetime
try:
   import cPickle as pickle
except:
   import pickle




def get_article_text(url):
    article_text = []
    html = urllib.urlopen(url).read()
    s = BeautifulSoup(html)
    for each in s.findAll('p'):
        try:
            if each.attrs['class'][0] == 'mol-para-with-font':
                article_text = article_text + nltk.word_tokenize(each.text)
        except KeyError:
            pass
    return article_text
    
def get_all_text(base_url, categorised_links):
    all_the_text = []
    for category in categorised_links:
        for link in categorised_links[category]:
            article_text = get_article_text('%s/%s' % (base_url, link))
            all_the_text = all_the_text + article_text
    return all_the_text

def link_scraper(base_url):
    connection = urllib.urlopen('%s/home/index.html' % base_url)
    dom = lxml.html.fromstring(connection.read())
    links = []
    for link in dom.xpath('//a/@href'):
        links.append(link)
    ## remove duplicate links, links that start with # or http
    links = set(links)
    links = [x for x in links if not x.startswith('#')]
    links = [x for x in links if not x.startswith('http')]
    links = [x for x in links if x.endswith('html')]
    
    ## default dict where key is category and value is list of links
    res_dict = {}
    for link in links:
        category = link.split('/')[1]
        if category in res_dict:
            res_dict[category].append(link)
        else:
            res_dict[category] = []
            res_dict[category].append(link)

    ## make a list of categories with less than 10 links and discard them
    ## also remove video links as not oging to handle these here
    discard = []
    for each in res_dict:
        if len(res_dict[each]) < 10:
            discard.append(each)
    for each in discard:
        del res_dict[each]

    for each in res_dict:
        random.shuffle(res_dict[each])
        #res_dict[each] = res_dict[each][:50]
    #    print each, len(res_dict[each])

    for each in res_dict:
        print each, len(res_dict[each])

    return res_dict

def get_top_2000_words(all_the_text):
    all_words = nltk.FreqDist(w.lower() for w in all_the_text)
    word_features = all_words.keys()[:2000]
    return word_features

def get_train_test(categorised_links):
    test_dict = {}
    train_dict = {}
    for category in categorised_links:
        number_links = len(categorised_links[category])
        i = (number_links - 1) / 2
        train_dict[category] = categorised_links[category][0:i] 
        test_dict[category] = categorised_links[category][i+1:]
    return train_dict, test_dict

def document_features(document, top_2000):
    document_words = set(document)
    features = {}
    for word in top_2000:
        features['contains(%s)' % word] = word in document_words
    return features

def document_features_eg(document_features, top_2000):
    document = get_article_text('http://www.dailymail.co.uk/health/article-2884783/Mother-two-drank-death-consuming-330-units-alcohol-WEEK-including-five-bottles-wine-day-vodka-breakfast.html')
    document_features = document_features(document, top_2000)
    print document_features

def get_train_test_features(train_dict, test_dict, base_url, top_2000):
    if os.path.exists('/Users/flashton/train_out.pick'):
        if os.path.exists('/Users/flashton/test_out.pick'):
            train_features = pickle.load(open('/Users/flashton/train_out.pick'))
            test_features = pickle.load(open('/Users/flashton/test_out.pick'))
    else:
        train_features = []
        test_features = []
        for category in train_dict:
            for link in train_dict[category]:
                article_text = get_article_text('%s/%s' % (base_url, link))
                features = document_features(article_text, top_2000)
                train_features.append((features, category))
        for category in test_dict:
            for link in test_dict[category]:
                article_text = get_article_text('%s/%s' % (base_url, link))
                features = document_features(article_text, top_2000)
                test_features.append((features, category))
        train_out = open('/Users/flashton/train_out.pick', 'wb')
        test_out = open('/Users/flashton/test_out.pick', 'wb')
        pickle.dump(train_features, train_out)
        pickle.dump(test_features, test_out)
    return train_features, test_features


def run_get_all_text(base_url, categorised_links):
    if os.path.exists('/Users/flashton/all_the_text.pick'):
        inp = open('/Users/flashton/all_the_text.pick')
        all_the_text = pickle.load(inp)
    else:
        all_the_text = get_all_text(base_url, categorised_links)
        output = open('/Users/flashton/all_the_text.pick', 'wb')
        pickle.dump(all_the_text, output)
    return all_the_text


def main():
    print datetime.datetime.now()
    base_url = 'http://www.dailymail.co.uk'
    categorised_links = link_scraper(base_url)
    ## the below functions just get all the text to get the most popular words (this will be biased toward more common articles)
    all_the_text = run_get_all_text(base_url, categorised_links)
    top_2000 = get_top_2000_words(all_the_text)
    train_dict, test_dict = get_train_test(categorised_links)
    train_features, test_features = get_train_test_features(train_dict, test_dict, base_url, top_2000)
    ## any features set is list of tuples where first elemtn is feature dict and second element is classifier
    classifier = nltk.NaiveBayesClassifier.train(train_features)
    print nltk.classify.accuracy(classifier, test_features)
    print classifier.show_most_informative_features(20)
    print datetime.datetime.now()


if __name__ == '__main__':
    main()
