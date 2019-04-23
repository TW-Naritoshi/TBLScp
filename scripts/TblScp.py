# -*- coding: utf-8 -*-
#時間測定用のデコレータ
from functools import wraps
import time
def stop_watch(func) :
    @wraps(func)
    def wrapper(*args, **kargs) :
        start = time.time()
        result = func(*args,**kargs)
        elapsed_time =  time.time() - start
        print(f"{func.__name__} is {elapsed_time} sec.")
        return result
    return wrapper
    
import requests
import urllib.request
from time import sleep
from bs4 import BeautifulSoup
import json
import sys
class TabelogScpapingBS:
    
    def __init__(self, interva_seconds=5):
        '''
        
        Parameters
        ----------
            interva_seconds: int
        '''
        
        self.interva_seconds = interva_seconds

    @stop_watch
    def get_shop_url_list(self, url):
        shop_url_list = []
        page_idx = 1
        while True:
            #------------------------------------------------------------
            #Get Page
            #------------------------------------------------------------
            res = requests.get(url)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            #------------------------------------------------------------
            #Show Target Count
            #------------------------------------------------------------
            
            #------------------------------------------------------------
            #Get Shop Name 
            #------------------------------------------------------------
            a_tag_list = soup.find_all('a', class_='list-rst__rst-name-target') # 店名、URL一覧

            for a_tag in a_tag_list:
                shop_name_url = {}
                shop_name_url['name'] = a_tag.text
                shop_name_url['url'] = a_tag.get('href')
                shop_url_list.append(shop_name_url)

            #------------------------------------------------------------
            #Move Next Page
            #------------------------------------------------------------
            page_idx += 1
            page_list = soup.find_all('a', class_='c-pagination__num', text=str(page_idx)) #ページングのリスト
            
            #If Next Page Not Found Then Exit Function
            if len(page_list) == 0:
                break
                
            #Get Next Page
            url = page_list[0].get('href')

            #Wait
            sleep(self.interva_seconds)

        return shop_url_list
        
    @stop_watch
    def get_shop_info_list(self, shop_url_list):
        shop_info_list = []
        for shop_url in shop_url_list:
            #------------------------------------------------------------
            #Get Page
            #------------------------------------------------------------
            url = shop_url['url']
            name = shop_url['name']
            res = requests.get(url)
            soup = BeautifulSoup(res.content, 'html.parser')

            #------------------------------------------------------------
            #Create Shop Info Dict
            #------------------------------------------------------------
            shop_info = {}
            shop_info['name'] = name
            shop_info['url'] = url

            #------------------------------------------------------------
            #Get Shop Info By Scrape
            #------------------------------------------------------------
            table = soup.find('table', class_='rstinfo-table__table')

            for item in table.find_all('tr'):
                header = item.find('th').text
                if header == '住所':
                    #住所
                    adress = item.find('p', class_='rstinfo-table__address').text
                    shop_info['adress'] = adress
                    #位置情報
                    map_url = item.find('img', class_='js-map-lazyload').get('data-original')
                    query = urllib.parse.urlparse(map_url).query
                    query_dic = urllib.parse.parse_qs(query)
                    location = query_dic['center'][0].split(',')
                    shop_info['location'] = location
                elif header == '支払い方法':
                    next_info = ''
                    is_card_ok, is_card_info_exists = False, False
                    for p_tag in item.find_all('p'):
                        if next_info == 'カード情報':
                            if p_tag.get('class') and 'rstinfo-table__notice' in p_tag.get('class'):
                                shop_info['card_info'] = p_tag.text.strip().replace('（','').replace('）','').split('、')
                                is_card_info_exists = True
                            next_info = 'Other Payment Info'

                        if p_tag.text.strip() == "カード可":
                            is_card_ok = True
                            next_info = 'カード情報'

                    #If Card OK and Card Info Not Found Then card_info add UnKnownCard        
                    if is_card_ok and is_card_info_exists == False:
                    	shop_info['card_info'] = ['利用可能なカード不明']

            #Set Return Value
            shop_info_list.append(shop_info)

            #Wait
            sleep(self.interva_seconds)

        return shop_info_list
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='TBL Get Data Script')
    parser.add_argument('page_url', help='Target Page URL')
    parser.add_argument('shop_url_file_path', help='Shop List Output File Path')
    parser.add_argument('shop_file_path', help='Shop Info Output File Path')
    parser.add_argument('-m', '--mode', default=0, help='Select Mode 0:Get Shop Url And Get Shop Info, 1:Get Shop Url, 2:Get Shop Info')
    #Get Args
    args = parser.parse_args()
    page_url = args.page_url
    shop_url_file_path = args.shop_url_file_path
    shop_file_path = args.shop_file_path
    shop_file_path = args.shop_file_path
    mode = args.mode
    print('Aargs Are {}'.format(args))

    #Create ScrapingObject
    scpaing = TabelogScpapingBS()

    if mode == '0' or mode == '1':
        print('Execute Get Shop Urls')
        #Get Shop Urls
        shop_url_list = scpaing.get_shop_url_list(page_url)
        shop_url_list_str = json.dumps(shop_url_list, ensure_ascii=False)
        with open(shop_url_file_path,'wb') as f:
            f.write(shop_url_list_str.encode("utf-8"))
    elif mode == '2':
        print('Read Shop Urls From File')
        with open(shop_url_file_path, 'r', encoding='utf-8') as f:
            shop_url_list = json.load(f)

    if mode == '0' or mode == '2':
        print('Execute Get Shop Info')
        #Get Shop Info
        shop_info_list = scpaing.get_shop_info_list(shop_url_list)
        shop_info_list_str = json.dumps(shop_info_list, ensure_ascii=False)
        with open(shop_file_path,'wb') as f:
            f.write(shop_info_list_str.encode("utf-8"))