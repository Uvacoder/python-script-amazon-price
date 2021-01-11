# Will be tracking the price of amazon product(s)

import requests
import os
import smtplib

import pandas as pd

from csv import writer
from bs4 import BeautifulSoup
from time import sleep
from dotenv import load_dotenv
from datetime import datetime
from playsound import playsound
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DOMAIN = 'https://www.amazon.ca'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

class Item():

    def __init__(self, name, price, id):
        self.name = name
        self.price = price
        self.id = id

def login(session):

    print('Logging in...')

    login_site = 'https://www.amazon.ca/gp/sign-in.html'

    response = session.get(login_site)
    soup = BeautifulSoup(response.content, 'lxml')

    # get all inputs required for login

    signin_data = {}
    form = soup.find('form', {'name': 'signIn'})
    for field in form.find_all('input'):
        try:
            signin_data[field['name']] = field['value']
        except:
            pass
    
    signin_data[u'email'] = os.getenv('EMAIL')
    signin_data[u'password'] = os.getenv('PASSWORD')
    
    # submit post request

    post_response = session.post('https://www.amazon.ca/ap/signin', data=signin_data)
    
    # test if login was successful

    post_soup = BeautifulSoup(post_response.content , 'lxml')

    if post_soup.find_all('title')[0].text == 'Your Account':
        print('Login Successful')
    else:
        print('Login Failed')
        exit()

def updateItem(data, tracker):
    
    ids = tracker.Id.tolist()
    index = ids.index(data[0])
    row = tracker.values[index].tolist()
    newrow = [row[0], row[1], "{:.2f}".format(row[2])]
    if newrow[2] == 'nan':
        newrow[2] = ''

    if newrow != data:
        with open('products.csv', 'r') as readfile:
            lines = readfile.readlines()
            for x, line in enumerate(lines):
                with open('temp.csv', 'a', newline='', encoding="utf-8") as writefile:
                    if x-1 == index:
                        writer(writefile).writerow(data)
                    else:
                        writefile.write(line.strip())
                        writefile.write('\n')
    
        if os.path.exists('products.csv'):
            os.remove('products.csv')
            os.rename('temp.csv', 'products.csv')
        else:
            print('error deleting file')

def addNewItems(session: requests.Session, tracker: pd.DataFrame) -> None:

    page = session.get(os.getenv('WISHLIST_URL'), headers=HEADERS)
    soup = BeautifulSoup(page.content, 'lxml')

    item_list = soup.find(id='wl-item-view')
    items = item_list.find_all('li')

    for item in items:

        id = item['data-itemid']
        name = item.find('h3', class_='a-size-base').find('a')['title']
        try:
            buy_below = str(item.find(id='itemCommentRow_'+id).text.strip())
        except:
            buy_below = ''
        
        # Check to see if the item is already in the csv file
        data = [id, name, str(buy_below)]
        if id in list(tracker.Id):
            updateItem(data, tracker)
            continue      

        with open('products.csv', 'a', newline='', encoding="utf-8") as file:
            writer(file).writerow(data)

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
                return ''
    return price[5::]

def send_email(item: Item) -> None:

    receiver_email = 'ngeldvis@gmail.com'
    sender_email = os.getenv('DEV_EMAIL')
    sender_password = os.getenv('DEV_PASSWORD')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Price Alert'

    message = f'An item on your wishlist dropped below asking price!\n{item.name} is now ${item.price}!'
    text = MIMEText(message, 'plain', 'utf-8')
    msg.attach(text)

    with smtplib.SMTP_SSL('64.233.184.108') as server:
        try:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string().encode('ascii'))
            print('Email sent.')
        except Exception as e:
            print('Email failed to send.')
            print(e)

def getPrices(session, tracker) -> None:
    
    page = session.get(os.getenv('WISHLIST_URL'), headers=HEADERS)
    soup = BeautifulSoup(page.content, 'lxml')

    item_list = soup.find(id='wl-item-view')
    items = item_list.find_all('li')

    for item in items:

        id = item['data-itemid']

        rownum = tracker['Id'].tolist().index(id)
        buy_below = str(tracker['Buy Below'].tolist()[rownum])

        try:
            priceTXT = item.find('span', class_='a-price-whole').text + item.find('span', class_='a-price-fraction').text
        except:
            continue

        if buy_below != 'nan':
            if float(priceTXT) <= float(buy_below):
                print('Price Alert!')
                playsound('rsc/notify.mp3')

                # try:
                name = item.find('h3', class_='a-size-base').find('a')['title']
                newItem = Item(name, float(priceTXT), id)
                send_email(newItem)
                # except:
                #     pass
        
def main(): 
    
    load_dotenv()

    session = requests.Session()
    session.headers = HEADERS
    
    # login(session)
    # ^------------^ 
    # unable to use if wishlist is private since too many login requests 
    # were sent and the sign-in process requires re-captcha challenges

    intervals = 1
    interval_length = 60 # seconds

    interval = 0
    while interval < intervals:

        # check to see if any new items have been added
        tracker = pd.read_csv('products.csv')
        addNewItems(session, tracker)

        # check the prices and if any have dropped below buy_below
        tracker = pd.read_csv('products.csv')
        getPrices(session, tracker)

        # sleep(interval_length)
        interval += 1 # update interval

main()