# Will be tracking the price of amazon product(s)

import requests
import os
import pandas as pd
import math

from bs4 import BeautifulSoup
from csv import writer
from glob import glob
from time import sleep
from dotenv import load_dotenv
from datetime import datetime

HEADERS = ({'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.61 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5'
})
DOMAIN = 'https://www.amazon.ca'


def login(session: requests.Session) -> None:

    loginSite = 'https://www.amazon.ca/gp/sign-in.html'

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


def addNewItems(session: requests.Session, tracker: pd.DataFrame) -> None:

    # check for new items in the wishlist

    page = session.get(os.getenv('WISHLIST_URL'), headers=HEADERS)
    soup = BeautifulSoup(page.content, 'lxml')

    title = soup.find(id='profile-list-name').get_text().strip()
    print(title)

    item_list = soup.find(id='wl-item-view')
    items = item_list.find_all('li')

    for item in items:

        # Check to see if the item is already in the csv file

        id = item['data-itemid']
        if id in list(tracker.id):
            continue

        name = item.find('h3', class_='a-size-base').find('a')['title'] 
        url = DOMAIN + item.find('h3', class_='a-size-base').find('a')['href']
        
        buy_below = item.find(id='itemCommentRow_'+id).text.strip()

        # Add Item

        with open('products.csv', 'a', newline='', encoding="utf-8") as file:
            writer(file).writerow([id, name, url, buy_below])


def getPrice(soup):
    try:
        price = soup.find(id='priceblock_ourprice').get_text().strip()
    except:
        try:
            price = soup.find(id='priceblock_saleprice').get_text().strip()
        except:
            try:
                price = soup.find(id='priceblock_dealprice').get_text().strip()
            except:
                price = ''
    return price


def getItemsInfo(session: requests.Session, tracker: pd.DataFrame) -> None:
    trackerURLs = tracker.url

    for x, url in enumerate(list(trackerURLs)):
        page = session.get(url, headers=HEADERS)
        soup = BeautifulSoup(page.content, 'lxml')

        id = soup.find(id='sourceCustomerOrgListItemID')['value']
        price = getPrice(soup)
        title = soup.find(id='productTitle').get_text().strip()
        
        for x, Id in enumerate(list(tracker.id)):
            if Id == id:
                buy_below = list(tracker.buybelow)[x]

        log = pd.DataFrame({
            'date': datetime.now().strftime('%d/%m/%y %H:%M'),
            'id': id,
            'url': url,
            'title': title,
            'buy_below': buy_below,
            'price': price
        }, index=[x])

    filename = 'history/checked_' + datetime.now().strftime('%d-%m-%y_%H-%M') + '.xlsx'
    log.to_excel(filename)



def main(): 
    load_dotenv()
    session = requests.Session()
    session.headers = HEADERS
    
    login(session)

    tracker = pd.read_csv('products.csv')

    addNewItems(session, tracker)
    getItemsInfo(session, tracker)


main()