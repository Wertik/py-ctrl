
import argparse
import network

def main():

    # Parse the command
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='<ip>:<port>')
    parser.add_argument('--timeout', help='connection timeout', type=int, default=3)
    parser.add_argument('--state', help='query perifery states', default=False, action='store_true')
    parser.add_argument('--cmd', help='command to send over');
    args = parser.parse_args()

    ip, port = args.host.split(':')[0], int(args.host.split(':')[1])

    conn = network.create_connection(ip, port, timeout=args.timeout)

    if not conn.ping():
        print('Failed to connect')
        return

    perifs = []

    # Print states
    if args.state:
        perifs = conn.update_states()
        
        print('\n')
        for perif in perifs:
            print(perif.compose_state())
        
    if args.cmd:
        conn.send_data(args.cmd)
        return

if __name__ == "__main__":
    main()