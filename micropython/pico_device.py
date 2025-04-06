import ujson
from machine import Pin,Timer,reset,PWM
import sys,select
import time
import random

"""
msg contain type
"cmd","response","event","log","ping","status"
"""

class TermReader:
    def __init__(self, byte_stream, buffer_bytes=100):
        self.stream, self.poller = byte_stream, select.poll()
        self.rb, self.rb_n, self.rb_len = bytearray(buffer_bytes), 0, buffer_bytes
        self.poller.register(self.stream, select.POLLIN)

    def rb_decode(self, a, b, max_char_len=6):
        'Returns decoded ring-buffer contents from a to b, and a-offset for next call'
        buff = self.rb[a:b] if a < b else self.rb[a:] + self.rb[:b]
        for n in range(max_char_len):
            try: result = buff[:-n or len(buff)].decode()
            except UnicodeError: pass
            else: return result, (self.rb_len + (b - n)) % self.rb_len
        else:
            if len(buff) > max_char_len: raise UnicodeError('Non-UTF-8 stream data')
        return '', a

    def read(self):
        n0, text = self.rb_n, list()
        poll_err = select.POLLHUP | select.POLLERR
        while ev := self.poller.poll(0):
            if ev[0][1] & poll_err or not (byte := self.stream.read(1)): break
            self.rb[self.rb_n] = byte[0]
            self.rb_n = (self.rb_n + 1) % self.rb_len
            if self.rb_n == n0:
                chunk, n0 = self.rb_decode(n0, self.rb_n)
                text.append(chunk)
        if self.rb_n != n0:
            chunk, self.rb_n = self.rb_decode(n0, self.rb_n)
            text.append(chunk)
        return ''.join(text).strip()

def btn_callback(*arg):
    print(ujson.dumps({"type":"event","status":"ok","event":"button_pressed"}))

def send_temp(*arg):
    temp = round(random.uniform(20.0, 30.0), 2)

    msg = {
        "type": "status",
        "status": "ok",
        "msg": "temp",
        "param":{
            "temp":temp
        }
    }

    print(ujson.dumps(msg))

term_reader = TermReader(sys.stdin.buffer)


led_pin = Pin(0,Pin.OUT)

led_pin2 = Pin(17,Pin.OUT)
PWM(led_pin2,10,duty_u16=30000)
btn = Pin(21,Pin.IN)

timer0 = Timer()
timer0.init(mode=Timer.PERIODIC,period=2000,callback=send_temp)



btn.irq(btn_callback,Pin.IRQ_FALLING)

while True:
    terminal_input = term_reader.read()
    if len(terminal_input)==0:
        continue

    try:
        msg:dict = ujson.loads(terminal_input)

    except Exception as e:
        print(ujson.dumps({"type":"error","error":e,"message":terminal_input}))
        continue

    try:
        type = msg.get('type')
        if type == "ping":
            print(ujson.dumps({"type":"response","status":"ok","response":"pong"}))


        if type == "cmd":

            cmd = msg.get('cmd')
            param:dict = msg.get('param',{})
            if cmd == "led":
                if param.get('state') == "on":
                    led_pin.on()
                if param.get('state') == "off":
                    led_pin.off()

            
    except Exception as e:
        print(ujson.dumps({"type":"error","error":e,"message":terminal_input}))
        pass
        