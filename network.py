import traceback
import socket

class Network:
    def __init__(self, server, port, mode, timeout=10, log=True):
        self.server = server
        self.port = port
        self.mode = mode
        
        self.connected = False
        self.conn = None
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(timeout)
        
        self.logging = log
        self.log = []
  
    @property
    def address(self):
        return (self.server, self.port)
        
    def add_log(self, log=None):
        if log is None:
            log = str(traceback.format_exc())
        log = f'\n{log}\n'
        if log in self.log:
            return
        self.log.append(log)
        
    def write_log(self):
        with open('net.log', 'w') as f:
            f.writelines(self.log)
        
    def get_connection(self):
        if self.conn:
            return self.conn
        return self.sock
        
    def start_network(self):
        if self.mode:
            self.connect()
        else:
            self.start_server()
        
    def connect(self):
        try:
            self.sock.connect(self.address)
            self.connected = True
            print('connected to server')
        except:
            self.add_log()
            self.sock.close()
            print('could not establish connection with server')
            
    def disconnect(self):
        self.connected = False
        print('lost connection')
            
    def start_server(self):
        try:
            self.sock.bind(self.address)
            self.sock.listen(1)
            conn, addr = self.sock.accept()
            self.conn = conn
            self.connected = True
            print('connected to', addr)
        except:
            self.add_log()
            self.sock.close()
            print('could not start server')
            
    def close(self):
        if self.conn is not None:
            self.conn.close()
        self.sock.close()
        
        if self.logging:
            self.write_log()
            
        if self.connected:
            self.connected = False
            print('connection closed')

    def _send(self, cmd):
        sent = False
        conn = self.get_connection()
        try:
            conn.sendall(bytes(cmd, encoding='utf-8'))
            sent = True
        except:
            self.add_log()
        return sent
        
    def send(self, cmd):
        if self.connected and cmd is not None:
            sent = self._send(cmd)
            if not sent:
                self.disconnect()
                
    def _recv(self):
        reply = None
        conn = self.get_connection()
        try:
            reply = conn.recv(4096).decode()
        except socket.timeout:
            reply = ''
        except:
            self.add_log()
            self.disconnect()
        return reply
      
    def recv(self):
        reply = None
        if self.connected:
            reply = self._recv()
            if reply is None:
                self.disconnect()        
        return reply
        
    def send_recv(self, cmd):
        self.send(cmd)
        return self.recv()
        
    def check_connection(self):
        return self._send('_')
         