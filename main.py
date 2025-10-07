from machine import Pin, PWM
from Motor import PicoGo
from ws2812 import NeoPixel
import utime
from ST7789 import ST7789

IR = Pin(5, Pin.IN)
M = PicoGo()
speed = 50
buzzer = PWM(Pin(4))

def getkey():
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
    
n = 0
Repeat="repeat"

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

# empty memory = black
# recording = blue
# repeat = green
# repeat step = light green 
# reverse = red
# reverse step = light red
# paused = white



class MovementRecors(object):
    def __init__(self, LED):
        self.LED = LED
        self.step = 0
        self.record = True
        self.lastKey=None
        self.lastKeyChange=None
        self.recordedMoves: list[tuple[int, int]] = []        

    def changeLast(self, key):
        if not self.record:
            return
        if self.lastKey == None or self.lastKeyChange == None:
            self.lastKey = key
            self.lastKeyChange = utime.ticks_us()
            return
        print(utime.ticks_us())
        print(self.lastKeyChange)
        self.recordedMoves.append((self.lastKey, utime.ticks_us() - self.lastKeyChange))
        self.step +=1
        
        if key == None:
            self.lastKey = None
            self.lastKeyChange = None
            return
        self.lastKey = key
        self.lastKeyChange = utime.ticks_us()
    
    def updateColor(self, action):
        if action in ['start', 'stop', 'nop']:
            self.LED.pixels_fill(self.LED.YELLOW if self.record else self.LED.WHITE)
        if action == 'repeat':
            self.LED.pixels_fill(self.LED.GREEN)
        if action == 'reverse':
            self.LED.pixels_fill(self.LED.RED)
        if action == 'repeatStep':
            self.LED.pixels_fill((75, 255, 75))
        if action == 'reverseStep':
            self.LED.pixels_fill((255, 50, 50))
        if action == 'blue':
            self.LED.pixels_fill(self.LED.BLUE)  
        if action == 'red':
            self.LED.pixels_fill(self.LED.RED)     
        self.LED.pixels_show()
    
    def clear(self):
        self.recordedMoves = []
        self.step = 0
        color = self.LED.BLUE if self.record else self.LED.WHITE;
        
        for i in range(3):
            self.LED.pixels_fill(self.LED.BLACK)
            self.LED.pixels_show()
            utime.sleep_ms(100)
            self.LED.pixels_fill(color)
            self.LED.pixels_show()
            utime.sleep_ms(100)
        
    def start(self):
        self.updateColor('start')
        print('start')
        self.record = True
        
    def stop(self):
        self.updateColor('stop')
        print('start')
        self.record = False
   
    def repeatStep(self, motor, speed):
        print('repeatStep',self.recordedMoves, self.step )
        if self.step >= len(self.recordedMoves):
            return
        print('exec')
        move = self.recordedMoves[self.step]
        
        if move[0] == Key2:
            motor.forward(speed)
        if move[0] == Key4:
            motor.left(20)
        if move[0] == Key6:
            motor.right(20)
        if move[0] == Key8:
            motor.backward(speed)
        if move[0] == Key1:
            self.sing()
        if move[0] == Key3:
            self.happyBeep()
        if move[0] == Key7:
            self.updateColor('blue')
        if move[0] == Key9:
            self.updateColor('red')        
        utime.sleep_us(move[1])
        motor.stop()
        utime.sleep_us(10000)
        
        self.step+=1
   
    def reverseStep(self, motor, speed):
        print('reverseStep',self.recordedMoves, self.step )
        if self.step <= 0:
            return
        print('exec')
        move = self.recordedMoves[self.step-1]
        
        if move[0] == Key2:
            motor.backward(speed)
        if move[0] == Key4:
            motor.right(speed)
        if move[0] == Key6:
            motor.left(speed)
        if move[0] == Key8:
            motor.forward(speed)
        utime.sleep_us(move[1])
        motor.stop()
        utime.sleep_us(10000)
        
        self.step-=1
        
    def repeat(self, motor, speed):
        self.updateColor('repeat')
        self.step=0
        for move in self.recordedMoves:
            self.repeatStep(motor, speed)
        utime.sleep_ms(250)
        self.updateColor('nop')
        
            
    
    def reverse(self, motor, speed):
        self.updateColor('reverse')
        self.step = len(self.recordedMoves)
        for move in reversed(self.recordedMoves):
            self.reverseStep(motor, speed)
        utime.sleep_ms(250)        
        self.updateColor('nop')
    
    def start_tone(self, freq):
        if freq == REST:
            buzzer.duty_u16(0)
        else:
            buzzer.freq(freq)
            buzzer.duty_u16(VOLUME)

    def stop_tone(self):
        buzzer.duty_u16(0)

    def tone(self, freq, dur_ms):
        self.start_tone(freq)
        utime.sleep_ms(dur_ms)
        self.stop_tone()
    
    def play_song(self, song):
        for freq, dur in song:
            self.tone(freq, dur)
        self.stop_tone()
    
    def sing(self):
        self.play_song([(C5, 100), (REST, 200), (E5, 100), (REST, 200), (G5, 100)])
    
    def happyBeep(self):
        self.play_song(
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


def red_to_green_st7789(progress):
    """
    Convert progress to ST7789-compatible RGB565 color
    Optimized for ST7789 display format
    
    Args:
        progress: Float from 0.0 (red) to 1.0 (green)
    
    Returns:
        16-bit RGB565 color value for ST7789
    """
    progress = max(0.0, min(1.0, progress))
    
    # Calculate 8-bit RGB values first
    red_8bit = int(255 * (1.0 - progress))
    green_8bit = int(255 * progress)
    blue_8bit = 0
    
    # Convert to RGB565 format (ST7789 native format)
    red_5bit = (red_8bit * 31) // 255      # 8-bit to 5-bit
    green_6bit = (green_8bit * 63) // 255  # 8-bit to 6-bit  
    blue_5bit = (blue_8bit * 31) // 255    # 8-bit to 5-bit
    
    # Pack into RGB565 format: RRRRR GGGGGG BBBBB
    rgb565 = (red_5bit << 11) | (green_6bit << 5) | blue_5bit
    
    return rgb565

def displaySpeed(speed):
    # 12-14  zelená
    lcd = ST7789()    #lcd.fill_rect(0,0,int(speed*240/100),300,int(((15-speed/10)*16)+7+speed/10))
    #green=
    rgb=   int(((30-speed/10)*64+40+speed/5)*32)
    gbrg = int(((rgb & 0x00FF)<<8) + ((rgb & 0xFF00)>>8)) 
    lcd.fill_rect(0,0,int(speed*240/100),300,gbrg)
    
    lcd.show()

magic = 1

if __name__ == '__main__':
    displaySpeed(speed)
    LED = NeoPixel()
    MR = MovementRecors(LED)
    MR.updateColor('nop')
    while True:
        key = getkey()
        
        if(key != None):
            print(key)
            if key != MR.lastKey and key in [Key1, Key2, Key3, Key4, Key6, Key7, Key8, Key9]:
                print(f"{key=}, {MR.lastKey=}")
                MR.changeLast(key)
                print(MR.recordedMoves)
            n = 0
            if key == Key2:
                M.forward(speed)
                print("forward")
            if key == Key4:
                M.left(20)
                print("left")
            if key == Key5:
                M.stop()
                print("stop")
            if key == Key6:
                M.right(20)
                print("right")
            if key == Key8:
                M.backward(speed)
                print("backward")
            if key == Play:
                MR.repeat(M, speed)
            if key == ChanelMinus:
                MR.clear()
            if key == Chanel:
                MR.start()
            if key == ChanelPlus:
                MR.stop()
            if key == Key0:
                MR.reverse(M, speed)
            if key == Prev:
                MR.updateColor('reverseStep')
                MR.reverseStep(M, speed)
                utime.sleep_ms(250)
                MR.updateColor('nop')
            if key == Next:
                MR.updateColor('repeatStep')
                MR.repeatStep(M, speed)
                utime.sleep_ms(250)
                MR.updateColor('nop')
            if key == Minus:
                speed = max(0, speed - 10)
                displaySpeed(speed)
                print(speed)
            if key == Plus:
                speed = min(100, speed + 10)
                displaySpeed(speed)
                print(speed)
            if key == Eq:
                speed = 50
                displaySpeed(speed)
            if key == Key1:
                MR.sing()
            if key == Key3:
                MR.happyBeep()
            if key == Key7:
                MR.updateColor('blue')
            if key == Key9:
                MR.updateColor('red')
            
            
        else:
            utime.sleep_us(10)
            n += 1
            if n > 800:
                if MR.lastKey is not None:
                    MR.changeLast(None)
                n = 0
                M.stop()

