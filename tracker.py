# Will be tracking the price of amazon product(s)

import requests
import os
import pandas as pd

from bs4 import BeautifulSoup
from glob import glob
from time import sleep
from dotenv import load_dotenv
from datetime import datetime

HEADERS = ({'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.61 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'})

def login() -> requests.Session:

    loginSite = 'https://www.amazon.ca/gp/sign-in.html'

    session = requests.Session()
    session.headers = HEADERS

    soup = BeautifulSoup(session.get(loginSite).content, 'lxml')

    data = {}
    form = soup.find('form', {'name': 'signIn'})
    for field in form.find_all('input'):
        try:
            data[field['name']] = field['value']
        except:
            pass
    
    data[u'email'] = os.getenv('EMAIL')
    data[u'password'] = os.getenv('PASSWORD')

    post_resp = session.post('https://www.amazon.ca/ap/signin', data=data)
    post_soup = BeautifulSoup(post_resp.content , 'lxml')
 
    if post_soup.find_all('title')[0].text == 'Your Account':
        print('Login Successfull')
    else:
        print('Login Failed')
        exit()

    return session

load_dotenv()

session = login()

page = session.get(os.getenv('WISHLIST_URL'), headers=HEADERS)
soup = BeautifulSoup(page.content, 'lxml')

title = soup.find(id='profile-list-name').get_text().strip()
print(title)

item_list = soup.find(id='wl-item-view')
items = item_list.find_all('li')

for item in items:   
    url = 'https://www.amazon.ca' + item.find('h3', class_='a-size-base').find('a')['href'] 
    subpage = session.get(url, headers=HEADERS)
    subsoup = BeautifulSoup(subpage.content, 'lxml')

    try:
        price = subsoup.find(id='priceblock_ourprice').get_text().strip()
    except:
        try:
            price = soup.find(id='priceblock_saleprice').get_text().strip()
        except:
            price = ''

    print(price)