import parts
import socket

class Connection:
    def __init__(self, ip, port, timeout=3):
        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.periferies = []

    def ping(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)

            print(f'Connecting to {self.ip}:{self.port}')

            return self.connect(sock)

    # Connect a given socket.
    def connect(self, sock):
        try:
            sock.connect((self.ip, self.port))
            return True
        except (TimeoutError, socket.timeout, ConnectionRefusedError, ConnectionError, OSError) as e:
            print(f'{self.ip}:{self.port} : Request timed out with timeout of {self.timeout}. Failed to connect.')
            return False

    def send_data(self, input, parse_data=False):
        print('\n')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            if not self.connect(sock):
                data = '500;Failed to connect.'
            else:
                print(f'Sending: {input}')

                sock.sendall(bytes(input + '\n\n', 'UTF-8')) # Add double newline to indicate data end
                data = sock.recv(1024).decode('UTF-8')

            if len(data) != 0:
                code = data.split(';')[0]
                msg = ';'.join(data.split(';')[1:]) if ';' in data else 'None'

                print(f'Full data: {data}\nStatus code: {code}\nMessage: {msg}')

                return data if not ';' in data or not parse_data else msg
            else:
                print('No response')
                return data
    
    ## Ping a device
    def ping(self):
        return self.send_data('chck').startswith('200')

    ## Send a control command
    def control(self, args):
        args = [str(a) for a in args]
        data = ';'.join(args)
        
        return self.send_data(f'ctrl;{data}').startswith('200')

    def get(self, pin):
        for obj in self.periferies:
            if obj.pin == pin:
                return obj
        return None

    # Fetch perifery states and properties
    def update_states(self):
        response = self.send_data('st', True)
        
        if len(response) == 0:
            print("Failed to fetch states.")
            return 

        states = []

        for str in response.split(','):
            obj = parts.parse_state(str)
            obj.conn = self
            states.append(obj)
        
        self.periferies = states
        return states

def create_connection(ip, port, timeout=3):
    return Connection(ip, port, timeout)