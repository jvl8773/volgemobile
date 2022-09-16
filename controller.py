import sys

import RPi.GPIO as gpio

from network import Network

class Controller(Network):
    frontleft = 17
    frontright = 22
    backleft = 23
    backright = 24
    pins = (frontleft, frontright, backleft, backright)
    front = (frontleft, frontright)
    back = (backleft, backright)
    left = (frontleft, backleft)
    right = (frontright, backright)
    
    lookup = {
        'a': pins,
        'f': front,
        'b': back,
        'l': left,
        'r': right,
        'fl': (frontleft,),
        'fr': (frontright,),
        'bl': (backleft,),
        'br': (backright,)
    }

    def __init__(self, server, port, mode):
        Network.__init__(self, server, port, mode, timeout=1)
        self.start_network()

        gpio.setmode(gpio.BCM)
        for p in Controller.pins:
            gpio.setup(p, gpio.OUT)
            gpio.output(p, False)
            
    def close(self):
        gpio.cleanup()
        super().close()

    def run(self):
        self._run()
        self.close()
        
    def _run(self):
        while self.connected:
            cmd = None

            cmd = self.recv()
            if cmd:
                try:
                    self.activate_motors(cmd)
                except:
                    self.add_log()

            self.send('1')

    def activate_motors(self, cmd):
        cmd = cmd.split('-')[-1]
        m, t = cmd.split()
        pins = None

        ms = m.split(',')
        pins = {p for m in ms for p in Controller.lookup.get(m)}
            
        if t == 'f':
            for p in pins:
                ison = not gpio.input(p)
                gpio.output(p, ison)

        elif t == '1':
            for p in pins:
                gpio.output(p, True)
                
        elif t == '0':
            for p in pins:
                gpio.output(p, False)
                
        elif t == 'x1':
            for p in Controller.pins:
                ison = p in pins
                gpio.output(p, ison)
        
        elif t == 'x0':
            for p in Controller.pins:
                ison = p not in pins
                gpio.output(p, ison)

if __name__ == '__main__':
    server = sys.argv[1]
    port = int(sys.argv[2])
    mode = int(sys.argv[3])
    c = Controller(server, port, mode)
    c.run()
