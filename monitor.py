import urllib.request
import json
import time
import Adafruit_CharLCD as LCD

crypto = ("bitcoin", "ethereum", "ripple", "litecoin", "neo", "stellar", "tron", "raiblocks", "verge", "dogecoin") #coins to monitor
monitorAll = False #Override crypto list and show all
limit = 100 #If monitor all, this is sets the number of top x=limit coins from coinmarketcap to monitor

currency = "USD" #USD/EUR
curSymbol = {"USD": "$", "EUR": "€"}

secondsPerCrypto = 5 #how many seconds before moving on to another crypto currency
cyclesBeforeRefresh = 5 #how many cycles through each crypto currency before refreshing

lcd = LCD.Adafruit_CharLCDPlate()
lcd.create_char(0, [4,10,10,17,17,17,31,0]) #Delta symbol
lcd.create_char(1, [24,8,24,21,29,7,1,1]) #24H symbol
lcd.create_char(2, [0,21,21,23,21,21,21,0]) #1H symbol

lcd.set_color(0.0, 0.0, 0.0)
for i in range(15): #Wait for internet connection, (by really just counting down 15 seconds, expecting it to be there by then)
    lcd.clear()
    lcd.message("Monitor in {}s..".format(15 - i))
    time.sleep(1)

monitoring = True
while monitoring:
    try:
        output = [] #To be sent to screen

        #Load API data:
        data = urllib.request.urlopen("https://api.coinmarketcap.com/v1/ticker/?limit={}&convert={}".format(limit, currency)).read().decode("utf8")
        parsed = json.loads(data)

        for coin in parsed:
            if coin["id"] in crypto:
                coinInfo = {}

                price = float(coin["price_" + currency.lower()])
                #Round price according to character length:
                if price >= 1000:
                    price = int(price)
                elif price >= 100:
                    price = round(price, 1)
                elif price >= 10:
                    price = round(price, 3)
                else:
                    price = round(price, 4)

                coinInfo["top"] = "{} ({})\n".format(coin["name"], coin["symbol"]) #what to write on top row
                coinInfo["bottom24h"] = "{}{} \x01\x00{}%".format(curSymbol[currency], price, coin["percent_change_24h"]) #what to write on the bottom row for 24H delta
                coinInfo["bottom1h"] = "{}{} \x02\x00{}%".format(curSymbol[currency], price, coin["percent_change_1h"]) #what to write on the bottom row for 1H delta

                output.append(coinInfo)
        
        for cycle in range(cyclesBeforeRefresh): #For each cycle though coins before refresh
            for coin in output:
                
                #show 1h change
                message = coin["top"] + coin["bottom1h"]
                lcd.clear()
                lcd.message(message)

                #show 24h change
                time.sleep(secondsPerCrypto / 2)
                message = coin["top"] + coin["bottom24h"]
                lcd.clear()
                lcd.message(message)

                time.sleep(secondsPerCrypto / 2)
        lcd.clear()
        lcd.message("Refreshing...")
    
    except Exception as e: #Most likely due to either coinmarketcap being down or lack of internet connection
        lcd.clear()
        lcd.message(str(e))
        time.sleep(5)
        lcd.clear()
        lcd.message("Retrying...")
