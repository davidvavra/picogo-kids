from machine import Pin, PWM
from Motor import PicoGo
from ST7789 import ST7789
from ws2812 import NeoPixel
import utime
import random

IR = Pin(5, Pin.IN)
M = PicoGo()
strip = NeoPixel()
Echo = Pin(15, Pin.IN)
Trig = Pin(14, Pin.OUT)
Trig.value(0)
Echo.value(0)
DSR = Pin(2, Pin.IN)
DSL = Pin(3, Pin.IN)
buzzer = PWM(Pin(4))
VOLUME = 20000  # 0..65535


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


def showtext(text):
    lcd = ST7789()
    lcd.fill(0xF232)
    lcd.text(text, 10, 10, 0xFF00)
    lcd.show()


def get_dist():
    Trig.value(1)
    utime.sleep_us(10)
    Trig.value(0)
    while Echo.value() == 0:
        pass
    ts = utime.ticks_us()
    while Echo.value() == 1:
        pass
    te = utime.ticks_us()
    distance = ((te - ts) * 0.034) / 2
    return distance


def random_color():
    return random.choice(
        (strip.RED, strip.YELLOW, strip.GREEN, strip.CYAN, strip.BLUE, strip.PURPLE)
    )


def random_state(state_weights):
    weight_total = sum(state_weights.values())
    chosen = random.randrange(0, weight_total)

    s = 0
    for state, weight in state_weights.items():
        s += weight
        if chosen < s:
            return state

    # this should never happen
    return None


# States


def Idle():
    d = get_dist()

    if d < 30:
        return random_state(
            {
                Rainbow: 20,
                Blink: 20,
                Sing: 10,
                ScanLeft: 20,
                ScanRight: 20,
                Back: 20,
            }
        )
    else:
        return random_state(
            {
                Rainbow: 20,
                Blink: 20,
                Sing: 10,
                SpinLeft: 5,
                SpinRight: 5,
                JerkLeft: 5,
                JerkRight: 5,
                ScanLeft: 20,
                ScanRight: 20,
                Move: 15,
                Chase: 15,
            }
        )


def Wait():
    utime.sleep(1 + random.random() * 3)
    return Idle


def Rainbow():
    strip.rainbow_cycle(0.005)
    strip.pixels_fill(strip.WHITE)
    strip.pixels_show()
    return Wait


def Blink():
    color = random_color()
    for i in range(10):
        strip.pixels_fill(strip.BLACK)
        strip.pixels_show()
        utime.sleep_ms(50)
        strip.pixels_fill(color)
        strip.pixels_show()
        utime.sleep_ms(50)
    return Wait


def scan(dir):
    M.setMotor(dir[0] * 3, dir[1] * 3)
    utime.sleep_ms(100)
    M.stop()

    utime.sleep_ms(100)

    md = get_dist()
    i = 2

    utime.sleep_ms(100)

    M.setMotor(*dir)
    utime.sleep_ms(200)
    M.stop()
    d = get_dist()
    if d > md:
        md = d
        i = 1

    utime.sleep_ms(100)

    M.setMotor(*dir)
    utime.sleep_ms(200)
    M.stop()
    d = get_dist()
    if d > md:
        i = 0

    utime.sleep_ms(100)

    M.setMotor(-dir[0], -dir[1])
    for x in range(i):
        utime.sleep_ms(200)
    M.stop()

    return random_state(
        {
            Move: 50,
            Chase: 50,
        }
    )


def ScanLeft():
    return scan((-20, 20))


def ScanRight():
    return scan((20, -20))


def Move():
    strip.pixels_fill(strip.BLUE)
    strip.pixels_show()
    ts = utime.ticks_us()
    M.forward(20)
    while (utime.ticks_us() - ts) < 10000000:
        d = get_dist()
        DR_status = DSR.value()
        DL_status = DSL.value()
        showtext(f"{d} {DR_status} {DL_status}")
        if (d <= 20) or (DR_status == 0) or (DL_status == 0):
            M.stop()
            return Happy
    M.stop()
    return Sad


def Chase():
    MAX_SPEED = 60
    MIN_SPEED = 20

    strip.pixels_fill(strip.PURPLE)
    strip.pixels_show()
    ts = utime.ticks_us()
    while (utime.ticks_us() - ts) < 5000000:
        d = get_dist()
        DR_status = DSR.value()
        DL_status = DSL.value()
        showtext(f"{d} {DR_status} {DL_status}")
        M.forward(min(MAX_SPEED, max(MIN_SPEED, d)))
        if (d <= 20) or (DR_status == 0) or (DL_status == 0):
            M.stop()
            return Happy
    M.stop()
    return Sad


def Happy():
    return random_state(
        {
            HappyLeft: 50,
            HappyRight: 50,
        }
    )


def HappyLeft():
    M.left(60)
    utime.sleep_ms(270)
    M.stop()
    return HappyBeep


def HappyRight():
    M.right(60)
    utime.sleep_ms(270)
    M.stop()
    return HappyBeep


def HappyBeep():
    strip.pixels_fill(strip.GREEN)
    strip.pixels_show()
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
    return Wait


def Sad():
    strip.pixels_fill(strip.RED)
    strip.pixels_show()
    tone(C4, 300)
    return Wait


def SpinLeft():
    M.left(60)
    utime.sleep_ms(270)
    M.stop()
    return Wait


def SpinRight():
    M.right(60)
    utime.sleep_ms(270)
    M.stop()
    return Wait


def JerkLeft():
    M.left(60)
    utime.sleep_ms(100)
    M.stop()
    return Wait


def JerkRight():
    M.right(60)
    utime.sleep_ms(100)
    M.stop()
    return Wait


def Back():
    strip.pixels_fill(strip.YELLOW)
    strip.pixels_show()
    M.backward(20)
    play_song(
        [
            (C6, 500),
            (REST, 500),
            (C6, 500),
            (REST, 500),
            (C6, 500),
            (REST, 500),
        ]
    )
    M.stop()
    return Wait


def Sing():
    play_song([(C5, 100), (REST, 200), (E5, 100), (REST, 200), (G5, 100)])
    return Wait


# Main


def main():
    state = Blink

    while state is not None:
        showtext(state.__name__)
        state = state()
        utime.sleep_ms(10)


if __name__ == "__main__":
    main()
