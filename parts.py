from tkinter.constants import HORIZONTAL
import PySimpleGUI as sg
import time
import network

# Mimic an enum with some constants
LED = 0
MOTOR = 1

TYPES = {
    LED: 'Led',
    MOTOR: 'Motor'
}

# --- Perifery classes

class Perifery:
    def __init__(self, pin, type):
        self.pin = pin
        self.type = type


class Led(Perifery):
    def __init__(self, pin, state, color):
        super().__init__(pin, LED)
        self.state = state
        self.color = color

    def draw(self, layout):
        layout.append([sg.Text(f'LED {self.pin}')])

        row = []

        row.append(sg.Graph(
            canvas_size=(80, 80), 
            graph_bottom_left=(0, 0), 
            graph_top_right=(80, 80), 
            background_color=sg.theme_background_color(), 
            key=f'_cnvs:{self.pin}_'
        ))

        # Switch and blink buttons
        row.append(sg.Column([
            [sg.Button('Switch', key=f'_led_switch:{self.pin}_')],
            [sg.Button('Blink', key=f'_led_blink:{self.pin}_')]
        ]))

        row.append(sg.Column([
            [sg.Button('On', key=f'_led_on:{self.pin}_')],
            [sg.Button('Off', key=f'_led_off:{self.pin}_')]]
        ))

        layout.append(row)
    
    def compose_state(self):
        return f'[{TYPES[self.type]}] {self.pin} : {"ON" if self.state else "OFF"} ({self.color})'

    def switch(self):
        return self.conn.control([self.pin, not self.state])

    def control(self, state):
        res = self.conn.control([self.pin, state])
        if res:
            self.state = state
        return res

    def blink(self, count, interval):
        for n in range(count * 2):
            self.control(not self.state)
            time.sleep(interval)

        self.control(False)
        

class Motor(Perifery):
    def __init__(self, pin, angle):
        super().__init__(pin, MOTOR)
        self.angle = angle

    def draw(self, layout):
        layout.append([sg.Text(f'MOTOR {self.pin}')])

        row = []

        row.append(sg.Slider(
            range=(0, 180),
            default_value=self.angle,
            resolution=5,
            key=f'_motor_angle:{self.pin}_',
            orientation='h',
            enable_events=True
            )
        )

        layout.append(row)

    def compose_state(self):
        return f'[{TYPES[self.type]}] {self.pin} : {self.angle}'

    def move(self, angle):
        return self.conn.control([self.pin, angle])

# Parse a state
def parse_state(str):
    arr = str.split(":");

    pin = int(arr[0]) # pin
    type = int(arr[1]) # type

    # Parse an LED state
    if type == LED:
        state = bool(int(arr[2]))
        color = arr[3]

        return Led(pin, state, color)

    # Parse a Motor state
    elif type == MOTOR:
        angle = int(arr[2])

        return Motor(pin, angle)
    
    else:
        raise TypeError('Invalid perifery type')