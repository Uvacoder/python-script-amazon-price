# Tracks the prices of items in an Amazon Wishlist

import os
import time
import pandas as pd

from time import sleep
from dotenv import load_dotenv

# Sending Emails
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.webdriver import WebDriver


load_dotenv()
FILENAME = os.getenv('FILENAME')


class Item():

    def __init__(self, name, price, id, want):
        self.name = name
        self.price = price
        self.id = id
        self.want = want

    def __repr__(self) -> str:
        txt = f'name: {self.name}, id: {self.id}, price: ${self.price:.2f}, asking price: ${self.want:.2f}'
        return txt


def load_site(url) -> WebDriver:


    opts = webdriver.ChromeOptions()
    opts.headless = True
    driver = webdriver.Chrome(options=opts)
    driver.get(url)
    sleep(1)

    elem = driver.find_element_by_tag_name('body')

    pagedowns = 10
    while pagedowns:
        elem.send_keys(Keys.END)
        time.sleep(0.2)
        pagedowns -= 1

    return driver


def update_item(data: pd.DataFrame, df: pd.DataFrame) -> None:
    
    ids = df.Id.tolist()
    index = ids.index(data[0])
    row = df.values[index].tolist()

    if row != data:
        try:
            df.at[index, 'Want'] = data[2]
            df.to_csv(FILENAME, index=False);
        except Exception as e:
            print('Error: failed to update file')
            print(e)


def search_items(driver: WebDriver, df: pd.DataFrame) -> None:

    items = driver.find_elements_by_css_selector('#wl-item-view li')
    
    for item in items:

        item_id = item.get_attribute('data-itemid')
        item_title = driver.find_element_by_id('itemName_'+item_id).get_attribute('title')
        item_subtitle = driver.find_element_by_id('item-byline-'+item_id).text
        item_name = item_title + ' ' + item_subtitle
        try:
            item_want = driver.find_element_by_id('itemComment_'+item_id).text.strip()
        except:
            item_want = ''
        
        new_item = [item_id, item_name, item_want]
       
        if item_id in list(df.Id):
            update_item(new_item, df)
            continue      

        data = pd.DataFrame([new_item], columns=['Id', 'Name', 'Want'])
        try:
            df = df.append(data, ignore_index=True, sort=False)
            df.to_csv(FILENAME, index=False)
        except Exception as e:
            print('Error: failed to update file')
            print(e)


def create_email_body(items: list) -> str:
    html = '''
        <p style="
            text-align: center; 
            color: #000000;
        ">Some items on your wishlist are under your asking price!</p>
        <table style="
            width: 50%;
            margin: 25px 0;
            border-collapse: collapse;
            border-radius: 5px 5px 0 0;
            overflow: hidden;
            margin: auto;
        ">
        <thead>
        <tr style="
            background-color: #fd983a;
            color: #ffffff;
            text-align: left;
        ">
        <th style="padding: 12px 15px; text-align: left;">Item</th>
        <th style="padding: 12px 15px; text-align: left;">Price</th>
        <th style="padding: 12px 15px; text-align: left;">Wanted Price</th>
        </tr>
        </thead>
        <tbody>'''
    for x, item in enumerate(items):
        if x == len(items) - 1: # last item in the list
            if x % 2 == 0: # even 
                html += f'''
                <tr style="
                    border-bottom: 1px solid #dddddd;
                    border-bottom: 2px solid #fd983a;
                    color: #000000;
                ">
                <td style="padding: 12px 15px; text-align: left;">{item.name}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.price:.2f}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.want:.2f}</td>
                </tr>'''
            else: # odd
                html += f'''
                <tr style="
                    border-bottom: 1px solid #dddddd; 
                    background-color: #f3f3f3;
                    border-bottom: 2px solid #fd983a;
                    color: #000000;
                ">
                <td style="padding: 12px 15px; text-align: left;">{item.name}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.price:.2f}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.want:.2f}</td>
                </tr>'''
        else:
            if x % 2 == 0: # even
                html += f'''
                <tr style="
                    border-bottom: 1px solid #dddddd;
                    color: #000000;
                ">
                <td style="padding: 12px 15px; text-align: left;">{item.name}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.price:.2f}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.want:.2f}</td>
                </tr>'''
            else: # odd
                html += f'''
                <tr style="
                    border-bottom: 1px solid #dddddd; 
                    background-color: #f3f3f3;
                    color: #000000;
                ">
                <td style="padding: 12px 15px; text-align: left;">{item.name}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.price:.2f}</td>
                <td style="padding: 12px 15px; text-align: left;">${item.want:.2f}</td>
                </tr>'''

    html += '''</tbody></table>'''

    return html


def send_email(items: list) -> None:

    # getting email values

    port = 465
    smtpserver = 'smtp.gmail.com'

    receiver_email = os.getenv('RECEIVER_EMAIL')
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')

    # create email body

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Weekly Wishlist Price Alert'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    if len(items) > 0:
        html = create_email_body(items)
        body = MIMEText(html, 'html')
        msg.attach(body)
    else:
        text = 'None of the items on your wishlist are under your asking price.'
        msg.attach(MIMEText(text, 'plain'))

    # sending email

    context = ssl.create_default_context()
    
    with smtplib.SMTP_SSL(smtpserver, port, context=context) as server:
        try:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print('Email sent.')
        except Exception as e:
            print('Email failed to send.')
            print(e)


def get_sale_items(driver: WebDriver, df: pd.DataFrame) -> list:

    items = driver.find_elements_by_css_selector('#wl-item-view li')

    found_items = []

    for item in items:

        item_id = item.get_attribute('data-itemid')
        item_title = driver.find_element_by_id('itemName_'+item_id).get_attribute('title')
        item_subtitle = driver.find_element_by_id('item-byline-'+item_id).text
        item_name = item_title + ' ' + item_subtitle

        rownum = df['Id'].tolist().index(item_id)
        want = df['Want'].tolist()[rownum]

        try: 
            priceA = driver.find_element_by_css_selector('#item_' + item_id + ' .a-price-whole').text
            priceB = driver.find_element_by_css_selector('#item_' + item_id + ' .a-price-fraction').text
            priceTXT = priceA + priceB
        except:
            continue

        if float(priceTXT) <= float(want):
            new_item = Item(item_name, float(priceTXT), item_id, want)
            found_items.append(new_item)
    
    return found_items


def main() -> None: 

    # check to see if any new items have been added
    df = pd.read_csv(FILENAME)
    driver = load_site(os.getenv('WISHLIST_URL'))
    search_items(driver, df)
    items = get_sale_items(driver, df) 
    send_email(items)


main()
