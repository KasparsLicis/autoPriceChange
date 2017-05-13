import requests
from bs4 import BeautifulSoup
import re
import datetime
import time
#import logging
#logging.basicConfig(level=logging.DEBUG)
http_proxy  = "http://127.0.0.1:8082"
https_proxy = "https://127.0.0.1:8082"
proxyDict = { 
              "http"  : http_proxy, 
              "https" : https_proxy
            }

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
##Somehow did not work
#ssslUrls = ['https://www.ss.lv/lv/transport/cars/bmw/5-series/filter/', 'https://www.ss.lv/lv/transport/cars/bmw/3-series/filter/', 'https://www.ss.lv/lv/transport/cars/audi/a4/filter/', 'https://www.ss.lv/lv/transport/cars/audi/a6/filter/', 'https://www.ss.lv/lv/transport/cars/volkswagen/golf-6/filter/', 'https://www.ss.lv/lv/transport/cars/volkswagen/golf-7/filter/', 'https://www.ss.lv/lv/transport/cars/volvo/v60/filter/','https://www.ss.lv/lv/transport/cars/volvo/xc60/filter/']
ssslUrlsxc60 = ['https://www.ss.lv/lv/transport/cars/volvo/xc60/filter/']
ssslUrlsv60 = ['https://www.ss.lv/lv/transport/cars/volvo/v60/filter/']
ssslUrlsbmw5 = ['https://www.ss.lv/lv/transport/cars/bmw/5-series/filter/']
ssslUrlsbmw3 = ['https://www.ss.lv/lv/transport/cars/bmw/3-series/filter/']
ssslUrlsa4 = ['https://www.ss.lv/lv/transport/cars/audi/a4/filter/']
ssslUrlsa6 = ['https://www.ss.lv/lv/transport/cars/audi/a6/filter/']
ssslUrlsg6 = ['https://www.ss.lv/lv/transport/cars/volkswagen/golf-6/filter/']
ssslUrlsg7 = ['https://www.ss.lv/lv/transport/cars/volkswagen/golf-7/filter/']

#494- petrol
#497- auto-gear-box
payloadList1 = [{"topt[18][min]": "2007", "topt[18][max]": "2008", "opt[34]": "494", "opt[35]": "497"}, {"topt[18][min]": "2009", "topt[18][max]": "2010", "opt[34]":"494", "opt[35]":"497"}, {"topt[18][min]": "2011", "topt[18][max]": "2012", "opt[34]":"494", "opt[35]":"497"}, {"topt[18][min]": "2013", "topt[18][max]": "2014", "opt[34]":"494", "opt[35]":"497"}, {"topt[18][min]": "2015", "topt[18][max]": "2016", "opt[34]":"494", "opt[35]":"497"}]

#initially planned to use as API. Can be used as standalone script as well
def sendDataToApi(manufacturer, model, yearPeriod, avgPrice):
    week = str(datetime.date.today().isocalendar()[1])
    year = str(datetime.datetime.now().year)
    #payload = {"year":year, "week":week, "manufacturer":manufacturer, "model":model, "yearPeriod":yearPeriod, "avaragePriceEur":avgPrice}
    #response = requests.post('http://localhost/', data=payload)
    #print response.content
    print year, week, manufacturer, model, yearPeriod, avgPrice

def returnCar(ssslUrls):
    result = ssslUrls.split('/')[6]
    return result

def returnCarModel(ssslUrls):
    result = ssslUrls.split('/')[7]
    return result

def returnPeriod(payloadList1):
    if '2007' in str(payloadList1):
        period = '2007-2008'
    if '2009' in str(payloadList1):
        period = '2009-2010'
    if '2011' in str(payloadList1):
        period = '2011-2013'
    if '2013' in str(payloadList1):
        period = '2013-2014'
    if '2015' in str(payloadList1):
        period = '2015-2016'
    return period
#remove smallest and biggest prices because they can be wrong
def improveAveragePrice(priceList):
    if (len(priceList))>6:
        priceList.remove(min(priceList))
        priceList.remove(max(priceList))
        if (len(priceList))>6:
            priceList.remove(min(priceList))
            priceList.remove(max(priceList))
    return priceList

def collectAll(ssslUrls):
    for ssslUrlsi in ssslUrls:
        car = returnCar(ssslUrlsi)
        model = returnCarModel(ssslUrlsi)
        for payloadList1i in payloadList1:
            period = returnPeriod(payloadList1i)
            priceList = []
            s = requests.session()
            #responseGet = s.get(ssslUrlsi, headers = headers, proxies=proxyDict, verify=False)
            #to act as normal user. First get and then post
            responseGet = s.get(ssslUrlsi, headers = headers, verify=False)
            time.sleep(1)
            responsePost = s.post(ssslUrlsi, data = payloadList1i, headers = headers, verify=False)

            #Post requests fail time to time. After long troubleshooting session found that post requests return 302 with redirect to initial page (https://www.ss.lv/lv/transport/cars/bmw/5-series/) without filter. Normal response must contain filter (https://www.ss.lv/lv/transport/cars/bmw/5-series/filter). Thats why we continue to send Post until there is filter in response. 
            while ('filter' not in responsePost.url):
                #print 'Not working Final destination: ', responsePost.url
                time.sleep(15)
                responsePost = s.post(ssslUrlsi, data = payloadList1i, headers = headers, verify=False)

            soup = BeautifulSoup(responsePost.content, 'html.parser')
            filterForm=soup.find(id="filter_frm")
            table=filterForm.find_all("table")
            tr=table[2].find_all("tr")

            #start only if there is more than 3 rows because first(hedder) and last(hidden line)
            if len(tr)>3:
                for trs in range (1,len(tr)-1): 
                    td=tr[trs].find_all("td")
                    try:
                        #bmw have one additional column
                        if car in ('bmw'):
                            price = td[7].get_text().encode('utf-8')
                        else:
                            price = td[6].get_text().encode('utf-8')
                        #remove all except numbers
                        price = re.sub('\D','',price)
                        #sometimes this fail. Do not know why. Thats why try, except
                        try:
                            price = float(price)
                            priceList.append(price)
                        except Exception as e:
                            print(e)
                    except Exception as e:
                        print(e)
                avgPrice=0
                priceList = improveAveragePrice(priceList)
                if len(priceList)>1:
                    avgPrice=sum(priceList)/len(priceList)
                sendDataToApi( car, model, period, avgPrice)     

collectAll(ssslUrlsa4)
time.sleep(5)
collectAll(ssslUrlsa6)
time.sleep(5)
collectAll(ssslUrlsbmw3)
time.sleep(5)
collectAll(ssslUrlsbmw5)
time.sleep(5)
collectAll(ssslUrlsg6)
time.sleep(5)
collectAll(ssslUrlsg7)
time.sleep(5)
collectAll(ssslUrlsv60)
time.sleep(5)
collectAll(ssslUrlsxc60)
