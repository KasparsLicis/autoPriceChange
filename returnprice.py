import requests
from bs4 import BeautifulSoup
import re
import datetime
import time

####
#CONFIGURATION ARE

#For troubleshooting
PROXYDICT = {'http' : 'http://127.0.0.1:2222', 'https' : 'https://127.0.0.1:2222'}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

SSLVURLS = ['https://www.ss.com/lv/transport/cars/bmw/5-series/filter/', 'https://www.ss.com/lv/transport/cars/bmw/3-series/filter/', 'https://www.ss.com/lv/transport/cars/audi/a4/filter/', 'https://www.ss.com/lv/transport/cars/audi/a6/filter/', 'https://www.ss.com/lv/transport/cars/volkswagen/golf-6/filter/', 'https://www.ss.com/lv/transport/cars/volkswagen/golf-7/filter/', 'https://www.ss.com/lv/transport/cars/volvo/v60/filter/','https://www.ss.com/lv/transport/cars/volvo/xc60/filter/']
#SSLVURLS = ['https://www.ss.com/lv/transport/cars/bmw/5-series/filter/', 'https://www.ss.com/lv/transport/cars/volvo/xc60/filter/']

#Payload id is designed to return only petrol and automatic gear box cars. 494- petrol 497- auto-gear-box
#
PAYLOADLIST = [{"topt[18][min]": "2007", "topt[18][max]": "2008", "opt[34]": "494", "opt[35]": "497"}, {"topt[18][min]": "2009", "topt[18][max]": "2010", "opt[34]":"494", "opt[35]":"497"}, {"topt[18][min]": "2011", "topt[18][max]": "2012", "opt[34]":"494", "opt[35]":"497"}, {"topt[18][min]": "2013", "topt[18][max]": "2014", "opt[34]":"494", "opt[35]":"497"}, {"topt[18][min]": "2015", "topt[18][max]": "2016", "opt[34]":"494", "opt[35]":"497"}]

### END OF CONFIGURATION ARE

#Initially planned to use this function as API request. Redesigned to use as standalone script
#return request year, week number, manufacturer, model, period, avgPrice
def sendDataToApi(manufacturer, model, yearPeriod, avgPrice):
    #payload = {"year":year, "week":week, "manufacturer":manufacturer, "model":model, "yearPeriod":yearPeriod, "avaragePriceEur":avgPrice}
    #response = requests.post('http://localhost/', data=payload)
    print (str(datetime.datetime.now().year), str(datetime.date.today().isocalendar()[1]), manufacturer, model, yearPeriod, avgPrice)

#return manufacturer from url, like bmw or audi
def returnCar(sslvUrls):
    return sslvUrls.split('/')[6]

#return model from url, like xc60
def returnCarModel(sslvUrls):
    return sslvUrls.split('/')[7]

#return car period list from payload
def returnPeriod(payloadList):
    if '2007' in str(payloadList):
        period = '2007-2008'
    if '2009' in str(payloadList):
        period = '2009-2010'
    if '2011' in str(payloadList):
        period = '2011-2013'
    if '2013' in str(payloadList):
        period = '2013-2014'
    if '2015' in str(payloadList):
        period = '2015-2016'
    return period

#function designed to improve avarage price. It will remove 2 smallest and biggest prices because they can be wrongly 
def improveAveragePrice(priceList):
    if (len(priceList))>6:
        priceList.remove(min(priceList))
        priceList.remove(max(priceList))
        if (len(priceList))>6:
            priceList.remove(min(priceList))
            priceList.remove(max(priceList))
    return priceList

#main function
def collectAll(SSLVURLS):
    for sslvurl in SSLVURLS:

        car = returnCar(sslvurl)
        model = returnCarModel(sslvurl)

        for payload in PAYLOADLIST:

            period = returnPeriod(payload)
            priceList = []

            #to act as normal user. First send getpause and then post
            s = requests.session()
            responseGet = s.get(sslvurl, headers = HEADERS, verify=False)
            #responseGet = s.get(sslvurl, headers = HEADERS, proxies=PROXYDICT, verify=False)
           
            time.sleep(1)
            #responsePost = s.post(sslvurl, data = payload, headers = HEADERS, proxies=PROXYDICT, verify=False)
            responsePost = s.post(sslvurl, data = payload, headers = HEADERS, verify=False)
            
            ###Post requests fail time to time. After long troubleshooting session found that post requests return 302 with redirect to initial page 
            # for example (https://www.ss.lv/lv/transport/cars/bmw/5-series/) without filter in url. 
            # Normal response must contain filter like (https://www.ss.lv/lv/transport/cars/bmw/5-series/filter). 
            # Thats why we are continueing to send Postand pause until there is filter in response.

            while ('filter' not in responsePost.url):
                
                time.sleep(15)
                responsePost = s.post(sslvurl, data = payload, headers = HEADERS, verify=False)
            
            #HTML parsing part
            soup = BeautifulSoup(responsePost.content, 'html.parser')
            filterForm=soup.find(id="filter_frm")
            table=filterForm.find_all("table")
            tr=table[2].find_all("tr")

            #Starts only if there is more than 3 rows because first is (hedder) and last is (hidden line)
            if len(tr)>3:
                for trs in range (1,len(tr)-1): 
                    td=tr[trs].find_all("td")
                    try:
                        #bmw have one more additional column
                        if car in ('bmw'):
                            price = td[7].get_text().encode('utf-8')
                        else:
                            price = td[6].get_text().encode('utf-8')

                        #remove all except numbers
                        price = re.sub('\D','',price)

                        #sometimes this fail. Do not know why.
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

collectAll(SSLVURLS)
