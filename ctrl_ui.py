from parts import LED
from PySimpleGUI.PySimpleGUI import TIMEOUT_EVENT, WINDOW_CLOSED, one_line_progress_meter
import PySimpleGUI as sg
import os
import re
import threading
import time
import network

#TODO: Change port
PORT = 80

device_window = None
devices = []

scanning = False

# Find devices using arp -a
def scan_devices():

    global scanning
    scanning = True

    cmd_out = os.popen("arp -a").read()
    line_arr = cmd_out.split('\n')
    line_count = len(line_arr)

    devices.clear()
    device_window['_dev_list_'].Update(values=devices)

    for i in range(0, line_count):
        y = line_arr[i]

        # Match the IP, filter anything that doesn't start with 10 or end with more than 2 digits.
        # This is a dumb thing to append less ips. Private IPs for a B class usually start with 10.x
        ip_out = re.findall('10.[0-9]+\.[0-9]+\.[0-9]{1,2}', y, re.M | re.I)
        if ip_out:
            ip = ip_out[0]

            try:
                conn = network.create_connection(ip, PORT, timeout=3)

                if not conn.ping():
                    continue

                if conn.ping():
                    devices.append(ip)
                    device_window['_dev_list_'].Update(values=devices)

            except TimeoutError:
                continue
    
    scanning = False

def blink_menu(conn, command_window, led_id):
    layout = [
        [sg.Column([[
            sg.Text('Blink count')],
            [sg.Slider(default_value=10, range=(1, 100), resolution=1, orientation='h', key='_count_')]
        ])],

         [sg.Column([[
            sg.Text('Blink interval')],
            [sg.Slider(default_value=1, range=(.1, 10), resolution=.1, orientation='h', key='_interval_')]
         ])],

         [sg.Button('Done', key='_done_')]
        ]

    window = sg.Window('Blink Control', layout)

    while True:

        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == '_done_':
            count = int(values['_count_'])
            interval = values['_interval_']

            thread = threading.Thread(target=blink_led, args=(conn, command_window, led_id, count, interval))
            thread.start()
            break

    window.close()

# Open a command menu for IP
def command_menu(ip, timeout):

    conn = network.create_connection(ip, PORT, timeout)

    if not conn.ping():
        sg.popup('Couldn\'t connect to device.')
        return

    try:
        conn.update_states()
    except TimeoutError:
        sg.popup('Couldn\'t connect to device.')
        return

    layout = [
        [sg.Text('Click the buttons to control the periferies.')]
    ]

    for perifery in conn.periferies:
        perifery.draw(layout);

    command_window = sg.Window(f'{ip}', layout).Finalize()

    for perifery in conn.periferies:
        if perifery.type == LED:
            command_window[f'_cnvs:{perifery.pin}_'].draw_circle((40, 40), 40, fill_color=perifery.color if perifery.state else 'gray', line_color=sg.theme_background_color())

    while True:
        event, values = command_window.read()

        if event == sg.WIN_CLOSED:
            break

        print(event)

        if event.startswith('_led_switch:'):
            pin = int(re.search('_led_switch:(\d+)_', event)[1])

            conn.get(pin).switch()
            update_state(conn, command_window, pin)
            continue

        if event.startswith('_led_on:'):
            pin = int(re.search('_led_on:(\d+)_', event)[1])

            conn.get(pin).control(True)
            update_state(conn, command_window, pin)
            continue

        if event.startswith('_led_off:'):
            pin = int(re.search('_led_off:(\d+)_', event)[1])

            conn.get(pin).control(False)
            update_state(conn, command_window, pin)
            continue

        if event.startswith('_led_blink:'):
            pin = int(re.search('_led_blink:(\d+)_', event)[1])

            blink_menu(conn, command_window, pin)
            continue

        if event.startswith('_motor_angle:'):
            pin = int(re.search('_motor_angle:(\d+)_', event)[1])
            angle = int(values[f'_motor_angle:{pin}_'])

            conn.get(pin).move(angle)
            continue

    command_window.close()

def update_state(conn, window, pin):
    perif = fetch_state(conn, pin)
    window[f'_cnvs:{pin}_'].draw_circle((40, 40), 40, fill_color=perif.color if perif.state else 'gray', line_color=sg.theme_background_color())

def fetch_state(conn, pin):
    conn.update_states()
    return conn.get(pin)
    
def blink_led(conn, command_window, pin, count, interval):
    conn.update_states()
    led = conn.get(pin)
    
    state = led.state

    for n in range(count * 2):
        state = not state

        if not conn.control([pin, state]):
            print('Blinking failed.')
            return

        update_state(conn, command_window, pin)
        time.sleep(interval)

    conn.control([pin, False])
    update_state(conn, command_window, pin)

def device_menu():
    sg.theme('DarkAmber')

    devices_lb = sg.Listbox(devices, key='_dev_list_', size=(25, 5), enable_events=True)

    layout = [ 
        [sg.Text('Select the device you want to control and click "Connect"')],
        [devices_lb, sg.Column([[sg.Text('Timeout (s)')], [sg.Slider(default_value=3, range=(1, 10), resolution=1, orientation='h', key='_timeout_')]])],
        [sg.Button('Connect', key='_conn_'), sg.Button('Refresh', key='_refr_')]
    ]

    global device_window
    device_window = sg.Window('Remote Control Panel', layout, finalize=True)

    threading.Thread(target=scan_devices).start()

    # main window loop begin
    while True:

        event, values = device_window.read()

        if event == sg.WIN_CLOSED:
            break

        if event == '_dev_list_':
            
            selected = values['_dev_list_']

            if len(selected) > 1:
                print('Select only one device please.')
            elif len(selected) < 1:
                print('Select a device please.')
            else:
                selected_device = selected[0]
                print('Selected ' + str(selected_device))

            continue

        # Connect button

        if event == '_conn_':
            if len(values['_dev_list_']) == 0:
                print('Select a device please.')
                continue

            selected = values['_dev_list_'][0]

            timeout = values['_timeout_']
            print(f'Set timeout to {timeout}')
            print(f'Connecting to {selected}:{PORT}')

            command_menu(selected, timeout)
            continue

        # Refresh

        if event == '_refr_':

            global scanning

            if scanning:
                sg.popup('Another scan already in progress.')
                continue

            threading.Thread(target=scan_devices).start()
            continue

    device_window.close()

def main():
    device_menu()

if __name__ == '__main__':
    main()