from machine import Pin, PWM
from Motor import PicoGo
from ws2812 import NeoPixel
import utime
from ST7789 import ST7789

# devices
IR = Pin(5, Pin.IN)
LED = NeoPixel()
LCD = ST7789() 
motor = PicoGo()
buzzer = PWM(Pin(4))

# variables
speed = 50
recordedSteps: list[int] = []
stepIndex = -1
color = LED.WHITE
n = 0

# keys
KEY_CH_MINUS= 69
KEY_CH= 70
KEY_CH_PLUS=71
KEY_PREV=68
KEY_NEXT=64
KEY_PLAY=67
KEY_MINUS=7
KEY_PLUS=21
KEY_EQ=9
KEY_0=22
KEY_100=25
KEY_200=13
KEY_1=12
KEY_2=24
KEY_3=94
KEY_4=8
KEY_5=28
KEY_6=90
KEY_7=66
KEY_8=82
KEY_9=74

# music notes
C4 = 262
Cs4 = 277
D4 = 294
Ds4 = 311
E4 = 330
F4 = 349
Fs4 = 370
G4 = 392
Gs4 = 415
A4 = 440
As4 = 466
B4 = 494
C5 = 523
Cs5 = 554
D5 = 587
Ds5 = 622
E5 = 659
F5 = 698
Fs5 = 740
G5 = 784
Gs5 = 831
A5 = 880
As5 = 932
B5 = 988
C6 = 1047
D6 = 1175
E6 = 1319
F6 = 1397
G6 = 1568
A6 = 1760
B6 = 1976
REST = 0
VOLUME = 20000  # 0..65535

def getKey():
    global IR
    if (IR.value() == 0):
        count = 0
        while ((IR.value() == 0) and (count < 100)): #9ms
            count += 1
            utime.sleep_us(100)
        if(count < 10):
            return None
        count = 0
        while ((IR.value() == 1) and (count < 50)): #4.5ms
            count += 1
            utime.sleep_us(100)
            
        idx = 0
        cnt = 0
        data = [0,0,0,0]
        for i in range(0,32):
            count = 0
            while ((IR.value() == 0) and (count < 10)):    #0.56ms
                count += 1
                utime.sleep_us(100)

            count = 0
            while ((IR.value() == 1) and (count < 20)):   #0: 0.56mx
                count += 1                                #1: 1.69ms
                utime.sleep_us(100)

            if count > 7:
                data[idx] |= 1<<cnt
            if cnt == 7:
                cnt = 0
                idx += 1
            else:
                cnt += 1

        if data[0]+data[1] == 0xFF and data[2]+data[3] == 0xFF:  #check
            return data[2]
        else:
            return("repeat")
        
def rgb_to_bgr565(rgb):
    r, g, b = (rgb)
    # 1. Standard RGB565 packing
    # Red: 5 bits, Green: 6 bits, Blue: 5 bits
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    
    # Pack into a 16-bit integer
    color = (r5 << 11) | (g6 << 5) | b5
    
    # 2. Swap the bytes (Little-Endian)
    # This is why Green becomes 0x1F00 or 0x001F in your library
    return ((color & 0xFF) << 8) | (color >> 8)

def displaySpeed():
    rgb = rgb_to_bgr565(color)
    LCD.fill(0)
    LCD.fill_rect(0,0,int(speed*240/100),300,rgb)
    LCD.show()
        
def updateColor(newColor):
    global color
    color = newColor
    LED.pixels_fill(color)
    LED.pixels_show()
    displaySpeed()
    
def start_tone(freq):
    if freq == REST:
        buzzer.duty_u16(0)
    else:
        buzzer.freq(freq)
        buzzer.duty_u16(VOLUME)

def stop_tone():
    buzzer.duty_u16(0)

def tone(freq, dur_ms):
    start_tone(freq)
    utime.sleep_ms(dur_ms)
    stop_tone()
    
def play_song(song):
    for freq, dur in song:
        tone(freq, dur)
    stop_tone()
    
def singUp():
    play_song([(C5, 100), (REST, 200), (E5, 100), (REST, 200), (G5, 100)])
        
def singDown():
    play_song([(G5, 100), (REST, 200), (E5, 100), (REST, 200), (C5, 100)])    
    
def singHappy():
    play_song(
            [
            (C5, 100),
            (REST, 50),
            (G5, 100),
            (C5, 100),
            (REST, 50),
            (G5, 100),
            (REST, 50),
            (C6, 100),
            ]
        )     

def runStep(key, forward):
    if key == KEY_2 and forward:
        motor.forward(speed)
    if key == KEY_2 and not forward:
        motor.backward(speed)
    if key == KEY_8 and forward:
        motor.backward(speed)
    if key == KEY_8 and not forward:
        motor.forward(speed)        
    if key == KEY_4 and forward:
        motor.left(20)
    if key == KEY_4 and not forward:
        motor.right(20)
    if key == KEY_6 and forward:
        motor.right(20)
    if key == KEY_6 and not forward:
        motor.left(20)
    if key == KEY_0:
        updateColor(LED.RED)
    if key == KEY_100:
        updateColor(LED.GREEN)
    if key == KEY_200:
        updateColor(LED.BLUE)
    if key == KEY_1:
        updateColor(LED.YELLOW)
    if key == KEY_3:
        updateColor(LED.CYAN)
    if key == KEY_5:
        updateColor(LED.WHITE)
    if key == KEY_7:
        updateColor(LED.PURPLE)
    if key == KEY_9:
        updateColor(LED.BLACK)
    if key == KEY_CH_MINUS:
        singDown()
    if key == KEY_CH_PLUS:
        singUp()       
    if key == KEY_CH:
        singHappy()  
        
def repeat():
    global recordedSteps
    for step in recordedSteps:
        runStep(step, True)
        utime.sleep(1)
    
def nextStep():
    global stepIndex
    global recordedSteps
    stepIndex += 1
    if (stepIndex >= len(recordedSteps)):
        stepIndex = 0
    runStep(recordedSteps[stepIndex], True)
    utime.sleep(1)
    
def previousStep():
    global stepIndex
    global recordedSteps
    stepIndex -= 1
    if (stepIndex < 0):
        stepIndex = 0
    runStep(recordedSteps[stepIndex], False)
    utime.sleep(1)

def clear():
    global recordedSteps
    recordedSteps = []

if __name__ == '__main__':
    updateColor(LED.WHITE)
    while True:
        key = getKey()
        if (key != None):
            print("key", key)
            n = 0
            if key in [KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0, KEY_100, KEY_200, KEY_CH, KEY_CH_MINUS, KEY_CH_PLUS]:
                runStep(key, True)
                recordedSteps.append(key)
            if key == KEY_PREV:
                previousStep()
            if key == KEY_NEXT:
                nextStep()
            if key == KEY_PLAY:
                repeat()
            if key == KEY_MINUS:
                speed = max(0, speed - 10)
                displaySpeed()
            if key == KEY_PLUS:
                speed = min(100, speed + 10)
                displaySpeed()
            if key == KEY_EQ:
                clear()
        else:
            utime.sleep_us(10)
            n += 1
            if n > 800:
                n = 0
                motor.stop()       