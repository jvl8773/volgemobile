import socket

pi_eth = '169.254.95.67'
comp_eth = '192.168.137.1'
port = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.settimeout(10)

def connect(sock, server, port):
    try:
        sock.connect((server, port))
        print('connected!')
    except socket.timeout:
        print('timed out')
    except Exception as e:
        print(f'error while connecting: {e}')
    finally:
        sock.close()

def start_server(sock, server, port):
    sock.bind((server, port))
    sock.listen(1)
    conn = None

    try:
        conn, addr = sock.accept()
        print('connected to', addr)
    except socket.timeout:
        print('timed out')
    finally:
        if conn:
            conn.close()
        sock.close()

start_server(sock, comp_eth, port)