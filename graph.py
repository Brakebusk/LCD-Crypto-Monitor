from PIL import Image
import urllib.request
from bs4 import BeautifulSoup #HTML parser
import io
import Adafruit_CharLCD as LCD
import time

class Graph:
    def __init__(self, coins, lcd):
        self.coins = coins #coins to monitor

        self.lcd = lcd

        self.LCDCharSize = (16, 2) #size of LCD by characters
        self.graphSize = (8, 1) #graphsize by 5*8 pixel characters (sadly chip only supports a maximum of 8 custom characters, [0] * [1] must not be >8)
        self.threshold = 1 #threshold when processing image for when to set character bit high state (0-255)

        self.charSets = {} #Will hold character sets for each coin
    
    def refresh(self): #Refresh graphs
        raw_data = urllib.request.urlopen("https://coinmarketcap.com/").read().decode("utf8")
        self.parsed_html = BeautifulSoup(raw_data, "html5lib")

        #Refresh character sets:
        for coin in self.coins:
            self.charSets[coin] = self._getCharacters(coin)


    def _getCharacters(self, coin): #returns characters for selected coin
        coin_id = "id-" + coin

        characters = {} #will hold output characters with position as key (x, y) => (0, 0) == top left
        
        row = self.parsed_html.find(id=coin_id) #find table row
        if row: #if found table row
            graphImg = row.find('img', attrs={'class':'sparkline'}) #find image tag
            if graphImg: #if found image tag
                graphImgSrc = graphImg['src'] #img source of 7d graph

                imgData = urllib.request.urlopen(graphImgSrc)
                imgFile = io.BytesIO(imgData.read())
                img = Image.open(imgFile).convert('RGBA').convert("L") #Load image into PIL as greyscale

                img = img.resize((self.graphSize[0] * 5, self.graphSize[1] * 8)) #resize image into graphSize
                #img.save(coin_id + ".png", "PNG")
                pixels = img.load() #create bitmap

                for r in range(self.graphSize[1]): #for each character row
                    for c in range(self.graphSize[0]): #for each character on that row
                        charData = []
                        for cr in range(8): #for each row in the character bitmap
                            crBin = "" #binary representation of character row
                            for cc in range(5): #for each column in the character bitmap
                                pixelX = c * 5 + cc #x-location in img pixels
                                pixelY = r * 8 + cr #y-location in img pixels

                                if pixels[pixelX, pixelY] > self.threshold:
                                    #color pixel
                                    crBin += "1"
                                else:
                                    #keep pixel dark
                                    crBin += "0"
                            #convert binary string to decimal int and add to charData
                            charData.append(int(crBin, 2))
                        characters[c, r] = charData #pass char data to output
        
        return characters

    def writeBitmap(self, coin):
        characters = self.charSets[coin]

        if len(characters) > 0: #non-empty charSet
            #write bitmap to LCD
            index = 0
            for r in range(self.graphSize[1]): #for each row
                for c in range(self.graphSize[0]): #for each char block
                    #Create chars:
                    self.lcd.create_char(index, characters[c, r]) #create characters
                    index += 1
                    
            #Write chars:
            cursorX = self.LCDCharSize[0] - self.graphSize[0] #write graph to the right of the lcd
            cursorBaseY = self.LCDCharSize[1] - self.graphSize[1] #ensure that graph is written as far down as possible

            #Write caption:
            self.lcd.set_cursor(0, cursorBaseY)
            self.lcd.message("7d line:")

            index = 0 #selected char RAM position
            adresses = ("\x00", "\x01", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07")
            for r in range(cursorBaseY, cursorBaseY + self.graphSize[1]): #for each row
                self.lcd.set_cursor(cursorX, r) #move cursor
                msg = ""
                for c in range(self.graphSize[0]): #for each char
                    msg += adresses[index]
                    index += 1
                self.lcd.message(msg) #write to selected row
