from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from time import sleep
import json
import datetime
from pyquery import PyQuery as pq
from lxml import html

chromeOptions = webdriver.ChromeOptions()
prefs = {"profile.managed_default_content_settings.images":2}
chromeOptions.add_experimental_option("prefs",prefs)
driver = webdriver.Chrome(chrome_options=chromeOptions)

# ---------------------- #
# -----------CONFIG----------- #
# ---------------------- #

# edit
_max_twts_per_page = 10000
_twts_per_page = 0

mode = 'stream' # 'stream' or 'account'

user = ''
lang = 'ar'
country = 'Riyadh%2C%20Kingdom%20of%20Saudi%20Arabia'
zone = "35" # zone miles
twitter_ids_filename = 'data/stream_'+country+'_'+lang+'_data.csv'

if mode == 'account':
    user = 'saudigosi'
    twitter_ids_filename = 'data/account_'+user+'_data.csv'
    
start = datetime.datetime(2015, 1, 1)  # year, month, day
end = datetime.datetime(2015, 10, 5)   # year, month, day

delay = 10  # time to wait on each page load before reading the page



# ---------------------- #
# -----------INIT----------- #
# ---------------------- #

twitter_res = open(twitter_ids_filename, 'a', encoding='utf8')

all_tweets = []
all_ids = []
_total = 0

days = (end - start).days + 1
id_selector = '.time a.tweet-timestamp'
tweet_selector = 'li.js-stream-item'
user = user.lower()

# load prev saved ids in the file
for rec in open(twitter_ids_filename, encoding='utf8'):
    if rec.strip() != "":
        recs = rec.strip().split("\t")
        if(len(recs) == 5):
            all_ids.append(str(recs[0]))

print("WARNING: We've already ",len(all_ids))

# methods
def format_day(date):
    day = '0' + str(date.day) if len(str(date.day)) == 1 else str(date.day)
    month = '0' + str(date.month) if len(str(date.month)) == 1 else str(date.month)
    year = str(date.year)
    return '-'.join([year, month, day])

def form_url(since, until, mode):
    url = ''
    if mode == 'stream':
        url = 'https://twitter.com/search?l=ar&q='
        url += 'near%3A"'+country+'"%20within%3A'+str(zone)+'mi%20since%3A'+since+'%20until%3A'+until+'include%3Aretweets&src=typd&lang='+lang
    elif mode == 'account':
        url = 'https://twitter.com/search?f=tweets&vertical=default&q='
        url += 'from%3A'+ user + '%20since%3A' + since + '%20until%3A' + until + 'include%3Aretweets&src=typd'
    return url

def increment_day(date, i):
    return date + datetime.timedelta(days=i)



# ---------------------- #
# -----------SCRAPPING----------- #
# ---------------------- #

for day in range(days):
    _twts_per_page = 0
    
    d1 = format_day(increment_day(start, 0))
    d2 = format_day(increment_day(start, 1))
    url = form_url(d1, d2, mode)
    
    if url == '':
        continue
    print("\n------------\nStart from day:",d1)
    driver.get(url)

    source = driver.page_source
    page = pq(html.fromstring(source))
    sleep(delay)

    try:
        
        for twt in page('div.js-stream-tweet'):
            twt = pq(twt)
            _id = str(twt.attr('data-tweet-id'))
            if _id != None and _id != "" and _id not in all_ids:
                data = {}
                data['id'] = _id
                data['screen_name'] = twt.attr('data-screen-name')
                data['user_id'] = twt.attr('data-user-id')
                data['text'] = twt('.js-tweet-text-container').text().strip().replace("\t"," ").replace("\n", " ").replace("\r", " ")
                data['time'] = twt('.js-short-timestamp').attr('data-time')
                
                if('text' in data and data['text'] != ""):
                    all_tweets.append(data)
                    all_ids.append(_id)
                    _twts_per_page += 1
        
        print('total: {}'.format(len(all_ids) + _total))
        
        _cont = True
        _miss = 0
        while _cont:
            print('scrolling down to load more tweets')
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            sleep(delay)
            
            #source = driver.find_element_by_tag_name('html').get_attribute('innerHTML')
            source = driver.page_source
            page = pq(html.fromstring(source))
            
            _found = False
            for twt in page('div.js-stream-tweet'):
                twt = pq(twt)
                _id = str(twt.attr('data-tweet-id'))
                if _id != None and _id != "" and _id not in all_ids:
                    data = {}
                    data['id'] = _id
                    data['screen_name'] = twt.attr('data-screen-name')
                    data['user_id'] = twt.attr('data-user-id')
                    data['text'] = twt('.js-tweet-text-container').text().strip().replace("\t"," ").replace("\n", " ").replace("\r", " ")
                    data['time'] = twt('.js-short-timestamp').attr('data-time')
                    
                    if('text' in data and data['text'] != ""):
                        all_tweets.append(data)
                        all_ids.append(_id)
                        _twts_per_page += 1
                        
                        _found = True
            
            # check if we should contiue
            if _found == False:
                _miss += 1
                
            if _miss >= 8:
                _cont = False
                
            if _twts_per_page >= _max_twts_per_page:
                _cont = False
            
            print('total: {}'.format(len(all_ids) + _total))
            
            # write each 100 records
            if len(all_tweets) >= 250:
                for rec in all_tweets:
                    twitter_res.write(rec['id']+"\t"+str(rec['time'])+"\t"+rec['screen_name']+"\t"+rec['user_id']+"\t"+rec['text']+"\n")
                twitter_res.close()
                twitter_res = open(twitter_ids_filename, 'a', encoding='utf8')
                all_tweets = []
                
                if len(all_ids) >= 10000:
                    _total += len(all_ids)
                    all_ids = []

    except NoSuchElementException:
        print('no tweets on this day')
    
    start = increment_day(start, 1)
    
# finish
if len(all_tweets) > 0:
    for rec in all_tweets:
        twitter_res.write(rec['id']+"\t"+str(rec['time'])+"\t"+rec['screen_name']+"\t"+rec['user_id']+"\t"+rec['text']+"\n")
    twitter_res.close()
