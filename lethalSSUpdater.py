import numpy as nm
import pytesseract
import cv2
from PIL import ImageGrab
from PIL import Image
import time
from statistics import mean

#for connecting to the google sheets
#Make sure you follow the readme to properly update lines 12 and 13 to connect to the Google Sheets
import gspread
gc = gspread.service_account(filename="creds.json")
gSheet = gc.open("Lethal Company Master Spreadsheet for Nerds").sheet1

#path of tesseract executable, replace with your tesseract.exe path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
cv2.namedWindow("Display 1", cv2.WINDOW_NORMAL)
cv2.namedWindow("Display 2", cv2.WINDOW_NORMAL)

#planet, weather, collected, paycheck, quota
possibleUpdate=[0,0,0,0,0]
confirmedUpdate=["Experimentation","Clear",0,0,130]
state = 1
zeroDoubleCheck = False
dayNum = 1
quotaNum = 1
printOnce = False

def imToString():
    #creating boundaries for the different capture areas
    global state
    capGreen = ImageGrab.grab(bbox=(300, 0, 1620, 1080))
    capCollected = ImageGrab.grab(bbox=(800, 790, 915, 840))
    capPaycheck = ImageGrab.grab(bbox=(1485, 700, 1650, 780))
    capQuota = ImageGrab.grab(bbox=(680,550,1300,800))
    capLanding = ImageGrab.grab(bbox=(550, 750, 1400, 850))
    capGreen.save("green.png")
    capCollected.save("collected.png")
    capPaycheck.save("paycheck.png")
    capQuota.save("quota.png")
    capLanding.save("landing.png")
    #watching two captures to either continue gathering information in the current state or detecting information that would lead to the next
    imageSearch = [['green.png', 'landing.png'],['collected.png', 'paycheck.png'],['green.png', 'landing.png'],['collected.png', 'paycheck.png'],['green.png', 'landing.png'],['collected.png', 'paycheck.png'],['green.png', 'landing.png'],['quota.png', 'paycheck.png']]
    startImage = cv2.imread(imageSearch[state - 1][0])
    startImage2 = cv2.imread(imageSearch[state - 1][1])

    #processing images
    images = [startImage, startImage2]
    processedImg1Color = 0;
    processedImg2Color = 0;
    image = 1
    for unprocessedImg in images:
        #increasing contrast
        lab = cv2.cvtColor(nm.array(unprocessedImg), cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(1, 1))
        cl = clahe.apply(l_channel)
        limg = cv2.merge((cl, a, b))
        enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        #setting color mask boundaries
        lower_green = nm.array([63, 150, 80])
        upper_green = nm.array([137, 255, 200])

        lower_red = nm.array([0, 0, 160])
        upper_red = nm.array([150, 170, 255])

        lower_lblue = nm.array([150, 150, 100])
        upper_lblue = nm.array([255, 230, 230])

        lower_gray = nm.array([100, 100, 100])
        upper_gray = nm.array([255, 255, 200])

        #creating masks and finalizing results
        maskGreen = cv2.inRange(enhanced_img, lower_green, upper_green)
        maskRed = cv2.inRange(enhanced_img, lower_red, upper_red)
        maskGrayWhite = cv2.inRange(enhanced_img, lower_gray, upper_gray)
        maskLBlue = cv2.inRange(enhanced_img, lower_lblue, upper_lblue)
        justGreen = cv2.bitwise_and(enhanced_img, enhanced_img, mask= maskGreen)
        justRed = cv2.bitwise_and(enhanced_img, enhanced_img, mask= maskRed)
        justGray = cv2.bitwise_and(enhanced_img, enhanced_img, mask= maskGrayWhite)
        justLBlue = cv2.bitwise_and(enhanced_img, enhanced_img, mask= maskLBlue)
        notGray = cv2.bitwise_not(justGray)
        redNoGray = cv2.bitwise_and(justRed, notGray)
        colorSearch = [[justGreen, justLBlue], [redNoGray, redNoGray], [justGreen, justLBlue], [redNoGray, redNoGray], [justGreen, justLBlue], [redNoGray, redNoGray], [justGreen, justLBlue], [redNoGray, redNoGray]]
        if (image == 1):
            processedImg1Color = colorSearch[state - 1][0]
            processedImg1 = cv2.cvtColor(processedImg1Color, cv2.COLOR_BGR2GRAY)
            image = 2
        elif (image == 2):
            processedImg2Color = colorSearch[state - 1][1]
            processedImg2 = cv2.cvtColor(processedImg2Color, cv2.COLOR_BGR2GRAY)
            image = 1

    #converting image to text
    if (state == 1 or state == 3 or state == 5 or state == 7):
        readText1 = pytesseract.image_to_string(
            processedImg1,
            lang='eng')
        data1 = -1
        conf1 = -1
        readText2 = pytesseract.image_to_string(
            processedImg2,
            lang='eng')
        data2 = -1
        conf2 = -1
    if (state == 2 or state == 4 or state == 6 or state == 8):
        readText1 = pytesseract.image_to_string(
            processedImg1,
            lang='eng3270',
            config='--psm 1')
        data1 = pytesseract.image_to_data(
            processedImg1,
            lang='eng3270',
            output_type='dict')
        conf1 = str(mean(data1["conf"]))
        readText2 = pytesseract.image_to_string(
            processedImg2,
            lang='eng3270',
            config='--psm 1')
        data2 = pytesseract.image_to_data(
            processedImg2,
            lang='eng3270',
            output_type='dict')
        conf2 = str(mean(data2["conf"]))
    cv2.imshow("Display 1", processedImg1)
    cv2.imshow("Display 2", processedImg2)
    cv2.waitKey(1)
    global possibleUpdate
    global confirmedUpdate
    global printOnce
    #checking for state changes and updating values
    if (state == 1 or state == 3 or state == 5 or state == 7):
        #check for planets
        if ("Experimentation" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "Experimentation"
        if ("Assurance" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "Assurance"
        if ("Vow" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "Vow"
        if ("Offense" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "Offense"
        if ("March" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "March"
        if ("Rend" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "Rend"
        if ("Dine" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "Dine"
        if ("Titan" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[0] = "Titan"
        if (("Company" or "building?") in readText1 and "Do you want" in readText1):
            possibleUpdate[0] = "Company"

        #allows for multiple status statements if things change
        if (("Company" or "building?") in readText1 and "Do you want" in readText1):
            possibleUpdate[0] = "Company"

        #check for weather
        if ("mild" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[1] = "Clear"
        elif ("rainy" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[1] = "Rainy"
        elif ("stormy" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[1] = "Stormy"
        elif ("flooded" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[1] = "Flooded"
        elif ("foggy" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[1] = "Foggy"
        elif ("eclipsed" in readText1 and ("Please CONFIRM" in readText1 or "or DENY" in readText1)):
            possibleUpdate[1] = "Eclipsed"

        if ("Please CONFIRM" in readText1 or "or DENY" in readText1):
            printOnce = False

        #check for confirm
        if ("Please enjoy" in readText1 or "your flight" in readText1 or "enjoy your" in readText1 or "is already" in readText1):
            confirmedUpdate[0] = possibleUpdate[0]
            confirmedUpdate[1] = possibleUpdate[1]
            if (confirmedUpdate[0] == 0):
                confirmedUpdate[0] = "MOON NOT FOUND"
            if (confirmedUpdate[1] == 0):
                confirmedUpdate[1] = "WEATHER NOT FOUND"
            if (printOnce == False):
                print("Potential Update: " + confirmedUpdate[0] + " - " + confirmedUpdate[1])
                printOnce = True

        #updates state and sends off info
        if ("WORLD" in readText2 or "Waiting for" in readText2 or "for crew" in readText2 or "Waiting" in readText2 or "seed" in readText2):
            update(confirmedUpdate[0], confirmedUpdate[1], 0, 0, 0)
            state = state + 1
            print("STATE: " + str(state) + " --- MOON: " + confirmedUpdate[0] + " --- WEATHER: " + confirmedUpdate[1])
            possibleUpdate = [0,0,0,0,0]
            printOnce = False

    elif (state == 2 or state == 4 or state == 6):
        stateChange = False
        readText1 = readText1.strip()
        if(readText1.isdigit() and possibleUpdate[2] != readText1 and float(conf1) > 12):
            possibleUpdate[2] = readText1
        elif(readText1 == '0'):
            zeroDoubleCheck = True
        elif((readText1.isdigit() and possibleUpdate[2] == readText1) or readText1 == '0' and zeroDoubleCheck == True):
            confirmedUpdate[2] = confirmedUpdate[2] + int(possibleUpdate[2])
            stateChange = True
            zeroDoubleCheck = False
        else:
            zeroDoubleCheck = False
        if (stateChange == True):
            update(0, 0, confirmedUpdate[2] , 0, 0)
            state = state + 1
            print("STATE: " + str(state) + " --- COLLECTED: " + str(confirmedUpdate[2]))
            possibleUpdate = [0, 0, 0, 0, 0]
            confirmedUpdate[2] = 0
        if (confirmedUpdate[0] == "Company"):
            state = state - 1

    elif (state == 8):
        #Handling sales
        readText2 = readText2.strip()
        if (readText2 != ""):
            if readText2[0] == "'":
                readText2 = readText2[1:]
        if (readText2.isdigit() and readText2 != possibleUpdate[3] and float(conf2) > 12):
            possibleUpdate[3] = readText2
            confirmedUpdate[3] = confirmedUpdate[3] + int(readText2)
        if (readText2 == ''):
            possibleUpdate[3] = 0
        #Handling quota
        originalText1 = '0'
        if readText1 != "":
            originalText1 = readText1
        readText1 = readText1[1:]
        readText1.strip()
        if (readText1.isdigit() and float(conf1) > 12 and originalText1[0] == "'"):
            possibleUpdate[4] = readText1
        if (confirmedUpdate[4] == possibleUpdate[4]):
            update(0, 0, 0, confirmedUpdate[3], confirmedUpdate[4])
            state = 1
            print("STATE: " + str(state) + " --- SOLD: " + str(
                confirmedUpdate[3]) + " --- QUOTA: " + str(confirmedUpdate[4]))
            possibleUpdate = [0, 0, 0, 0, 0]
            confirmedUpdate[3] = 0
        if (readText1.isdigit() and int(possibleUpdate[4]) != int(confirmedUpdate[4])):
            confirmedUpdate[4] = possibleUpdate[4]



def update(planet, weather, collected, sold, quota):
    global dayNum
    global quotaNum
    #edit the following to change which cells are updated in the Google Sheets
    if(planet != 0 and ((dayNum%3) != 1 or dayNum == 1)):
        gSheet.update_cell(dayNum + 1, 6, planet)
    if(weather != 0 and ((dayNum%3) != 1 or dayNum == 1)):
        gSheet.update_cell(dayNum + 1, 7, weather)
    if(collected != 0):
        gSheet.update_cell(dayNum + 1, 8, collected)
        dayNum = dayNum + 1
    if(sold != 0):
        gSheet.update_cell((3*quotaNum)-1, 10, sold)
    if(quota != 0):
        quotaNum = quotaNum + 1
        gSheet.update_cell((3*quotaNum)-1, 5, quota)



#### MAIN ####
while (1 == 1):
    imToString()

