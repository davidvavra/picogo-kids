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
color = LED.White

# keys
ChanelMinus = 69
Chanel= 70
ChanelPlus=71
Prev=68
Next=64
Play=67
Minus=7
Plus=21
Eq=9
Key0=22
Key100=25
Key200=13
Key1=12
Key2=24
Key3=94
Key4=8
Key5=28
Key6=90
Key7=66
Key8=82
Key9=74

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
    
def displaySpeed():
    LCD.fill_rect(0,0,int(speed*240/100),300,color)
    LCD.show()
        
def updateColor(color):
    color = color
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
    play_song([(C5, 100), (REST, 200), (E5, 100), (REST, 200), (G5, 100)])    
    
def singHappy(self):
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
    if key == Key2 and forward:
        motor.forward(speed)
    if key == Key2 and not forward:
        motor.backward(speed)
    if key == Key8 and forward:
        motor.backward(speed)
    if key == Key8 and not forward:
        motor.forward(speed)        
    if key == Key4 and forward:
        motor.left(20)
    if key == Key4 and not forward:
        motor.right(20)
    if key == Key6 and forward:
        motor.right(20)
    if key == Key6 and not forward:
        motor.left(20)
    if key == Key0:
        updateColor(LED.RED)
    if key == Key100:
        updateColor(LED.GREEN)
    if key == Key200:
        updateColor(LED.BLUE)
    if key == Key1:
        updateColor(LED.YELLOW)
    if key == Key3:
        updateColor(LED.CYAN)
    if key == Key5:
        updateColor(LED.WHITE)
    if key == Key7:
        updateColor(LED.PURPLE)
    if key == Key9:
        updateColor(LED.BLACK)
    if key == ChannelMinus:
        singDown()
    if key == ChannelPlus:
        singUp()       
    if key == Channel:
        singHappy()
    utime.sleep_us(speed)
    motor.stop()
    utime.sleep_us(10000)    
        
def repeat():
    for step in recordedSteps:
        runStep(step, true)
    
def nextStep():
    stepIndex += 1
    if (stepIndex >= stepIndex.size):
        stepIndex = 0
    runStep(recordedSteps[stepIndex], true)
    
def previousStep():
    stepIndex -= 1
    if (stepIndex < 0):
        stepIndex = 0
    runStep(recordedSteps[stepIndex], false)

def clear():
    recordedSteps = []

if __name__ == '__main__':
    updateColor(Color.White)
    while True:
        key = getkey()
        
        if (key != None):
            if key in [Key1, Key2, Key3, Key4, Key6, Key7, Key8, Key9, Key0, Key100, Key200, ChannelMinus, ChannelPlus, Channel]:
                runStep(key, true)
                recordedSteps += key
            if key == Prev:
                previousStep()
            if key == Next:
                nextStep()
            if key == Play:
                repeat()
            if key == Minus:
                speed = max(0, speed - 10)
                displaySpeed()
            if key == Plus:
                speed = min(100, speed + 10)
                displaySpeed()
            if key == Eq:
                clear()
