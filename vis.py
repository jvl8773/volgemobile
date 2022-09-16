import os
import sys
import threading
import traceback

import pygame as pg
import ui

import audio_classifier as ac

def init():
    Mic.set_image()
    Info_Box.set_image()
    
class Info_Box(ui.Image):
    IMAGE = None
    NAME_RECT = None
    INFO_RECT = None
    
    @classmethod
    def set_image(cls):
        w = 300
        h = 100
        o = 5
        
        base = pg.Surface((w, h)).convert()
        name_rect = pg.Rect(0, 0, w, 30)
        pg.draw.rect(base, (255, 255, 255), name_rect)
        r = pg.Rect(0, 0, w, h)
        pg.draw.rect(base, (255, 255, 255), r, width=o)
        
        info_rect = pg.Rect(0, name_rect.height, w, h - name_rect.height)
        
        cls.IMAGE = base
        cls.NAME_RECT = name_rect
        cls.INFO_RECT = info_rect

    def __init__(self, name):
        super().__init__(Info_Box.IMAGE)
        
        self.name_rect = ui.Position(rect=Info_Box.NAME_RECT.copy())
        self.add_child(self.name_rect, current_offset=True)
        self.info_rect = ui.Position(rect=Info_Box.INFO_RECT.copy())
        self.add_child(self.info_rect, current_offset=True)
        
        self.name = ui.Textbox(name, fgcolor=(0, 0, 0))
        self.name.rect.midleft = self.name_rect.rect.midleft
        self.name.rect.x += 5
        self.name.fit_text(self.name_rect.rect.inflate(-5, -5))
        self.add_child(self.name, current_offset=True)
        
        self.info = (
            ui.Textbox('prediction: ', tsize=15),
            ui.Textbox('amplitude: ', tsize=15),
            ui.Textbox('confidence: ', tsize=15)
        )
        
        step = 2
        y = self.info_rect.rect.y + step
        for t in self.info:
            t.rect.top = y
            t.rect.x = self.rect.x + 5
            self.add_child(t, current_offset=True)
            y += t.rect.height + step
            
    def update_info(self, prediction, amplitude, confidence):
        self.info[0].set_message(f'prediction: {prediction}')
        self.info[1].set_message(f'amplitude: {amplitude}')
        self.info[2].set_message(f'confidence {confidence}')
            
    def update(self):
        super().update()
        self.name.update()
        for t in self.info:
            t.update()

    def draw(self, surf):
        super().draw(surf)
        self.name.draw(surf)
        
        for t in self.info:
            t.draw(surf)

class Mic(ui.Image):
    IMAGE = None
    
    @classmethod
    def set_image(cls):
        cls.IMAGE = pg.image.load('visual/img/mic.png').convert()
        
    def __init__(self, mic, quad):
        self.mic = mic
        self.quad = quad
        self.info = Info_Box(getattr(self.mic, 'name', ''))
        
        self.pause_button = ui.Button.text_button('stop', padding=(20, 2), func=self.pause)
        self.spec_button = ui.Button.text_button('view spec', padding=(20, 2), func=self.spec_menu)

        super().__init__(Mic.IMAGE)
        
        self.info.rect.midtop = self.rect.midbottom
        self.info.rect.y += 10
        self.add_child(self.info, current_offset=True)
        
        self.pause_button.rect.midleft = self.rect.midright
        self.pause_button.rect.x += 5
        self.add_child(self.pause_button, current_offset=True)
        
        self.spec_button.rect.topleft = self.pause_button.rect.topright
        self.spec_button.rect.x += 5
        self.add_child(self.spec_button, current_offset=True)
    
    def set_quad(self, quad):
        self.quad = quad
        if self.mic:
            self.mic.set_quad(quad)

    def pause(self):
        self.mic.set_recording(not self.mic.recording)
        if not self.mic.recording:
            self.pause_button.object.set_message('record')
        else:
            self.pause_button.object.set_message('stop')
            
    def get_circle(self):
        amp = self.mic.amplitude * 1e4
        red = min(255, int(amp))
        color = (red, 0, 0)
        radius = (red / 255) * 100
        return (color, radius)
        
    def events(self, events):
        if self.mic:
            self.pause_button.events(events)
            self.spec_button.events(events)
        
    def update(self):
        super().update()
        if self.mic:
            self.info.update_info(self.mic.prediction, self.mic.amplitude * 1e3, self.mic.confidence)
            self.info.update()
            self.pause_button.update()
            self.spec_button.update()
        
    def draw(self, surf):
        if self.mic:
            if self.mic.recording:
                color, r = self.get_circle()
                pg.draw.circle(surf, color, self.rect.center, r)
        super().draw(surf)
        if self.mic:
            if self.mic.recording:
                self.info.draw(surf)
            self.pause_button.draw(surf)
            self.spec_button.draw(surf)
            
    def get_objects(self):
        objects = []
        
        w, h = ui.get_size()
        
        path = self.mic.img_path
        img = pg.image.load(path).convert()
        img = pg.transform.scale(img, (0.1 * img.get_width(), 0.1 * img.get_height()))
        i = ui.Image(img)
        i.rect.center = (w // 2, h // 2)
        objects.append(i)
        
        b = ui.Button.text_button('X', color2=(0, 0, 0), fgcolor=(255, 0, 0), tag='break')
        b.rect.bottomleft = i.rect.topright
        b.rect.x += 5
        b.rect.y -= 5
        objects.append(b)
        
        return objects
            
    def spec_menu(self):
        path = self.mic.img_path
        try:        
            m = Spec_Menu(get_objects=self.get_objects)
            m.run()
        except FileNotFoundError:
            pass
      
class Spec_Menu(ui.Menu):
    def quit(self):
        self.running = False
 
def get_notification():
    objects = []
    
    w, h = ui.get_size()
    
    i = pg.image.load('visual/img/driver.png').convert()
    i = pg.transform.smoothscale(i, (i.get_width() - 50, i.get_height() - 50))
    i = ui.Image(i)
    i.set_background((0, 0, 0))
    i.rect.center = (w // 2, h // 2)
    objects.append(i)
    
    hazard = ui.Textbox.static_textbox('!!', tsize=200, fgcolor=(255, 0, 0))
    hazard.set_visible(False)
    objects.append(hazard)
    
    t = ui.Textbox('', tsize=35)
    t.rect.midtop = i.rect.midbottom
    objects.append(t)
    
    def update():
        ac = Display.ac
        mics = ac.activated_mics.copy()
        if mics:
            p = mics[0].prediction.replace('_', ' ')
            if p not in t.message:
                t.set_message(f'hazard: {p}')
            t.set_visible(True)
            hazard.set_visible(True)
            
            if len(mics) == 1:
                m = mics[0]
                if m.quad == 'fl':
                    hazard.rect.bottomright = i.rect.topleft
                elif m.quad == 'fr':
                    hazard.rect.bottomleft = i.rect.topright
                elif m.quad == 'bl':
                    hazard.rect.topright = i.rect.bottomleft
                elif m.quad == 'br':
                    hazard.rect.topleft = i.rect.bottomright
            else:
                m1, m2 = mics[:2]
                if 'f' in m1.quad and 'f' in m2.quad:
                    hazard.rect.midbottom = i.rect.midtop
                elif 'b' in m1.quad and 'b' in m2.quad:
                    hazard.rect.midtop = i.rect.midbottom
                elif 'l' in m1.quad and 'l' in m2.quad:
                    hazard.rect.midright = i.rect.midleft
                elif 'r' in m1.quad and 'r' in m2.quad:
                    hazard.rect.midleft = i.rect.midright

        else:
            t.set_visible(False)
            hazard.set_visible(False)
            
    t.set_func(update)

    return objects
    
def set_screen(display):
    objects = []
    
    w, h = ui.get_size()
    
    points = ((w // 4, h // 4), (3 * w // 4, h // 4), (w // 4, 3 * h // 4), (3 * w // 4, 3 * h // 4))
    quads = ('fl', 'fr', 'bl', 'br')
    mics = {}
    for i, p in enumerate(points):
        q = quads[i]
        m = Mic(Display.ac.get_mic_by_quad(q), q)
        m.rect.center = p
        mics[q] = m
        objects.append(m)
        
    def swap(p1, p2):
        m1 = None
        m2 = None
        for m in mics.values():
            if m.rect.collidepoint(p1):
                m1 = m
            elif m.rect.collidepoint(p2):
                m2 = m
        q1 = m1.quad
        q2 = m2.quad
        m1.rect.center = p2
        m1.set_quad(q2)
        m2.rect.center = p1
        m2.set_quad(q1)
        
    lr = pg.Surface((100, 20)).convert()
    lr.set_colorkey((0, 0, 0))
    l = ui.Image_Manager.get_arrow('l', (20, 20))
    r = pg.transform.flip(l, True, False)
    lr.blit(l, (0, 0))
    lr.blit(r, (80, 0))
    
    ud = pg.Surface((20, 100)).convert()
    ud.set_colorkey((0, 0, 0))
    u = ui.Image_Manager.get_arrow('u', (20, 20))
    d = pg.transform.flip(u, False, True)
    ud.blit(u, (0, 0))
    ud.blit(d, (0, 80))

    pairs = ((mics['fl'], mics['fr']), (mics['fl'], mics['bl']), (mics['fr'], mics['br']), (mics['bl'], mics['br']))
    for m1, m2 in pairs:
        p1 = m1.rect.center
        p2 = m2.rect.center
        x1, y1 = p1
        x2, y2 = p2
        if m1.quad[0] == m2.quad[0]:
            img = lr
            pad = (20, 10)
        else:
            img = ud
            pad = (10, 20)
        b = ui.Button.image_button(img, padding=pad, func=swap, args=[p1, p2], border_radius=10)
        x = (x1 + x2) // 2
        y = (y1 + y2) // 2
        b.rect.center = (x, y)
        objects.append(b)

    i = ui.Input((50, 30), message='a 0', color=(255, 255, 255), fgcolor=(0, 0, 0))
    objects.append(i)

    def send_cmd():
        cmd = i.get_message()
        if cmd:
            Display.ac.send(cmd)
    
    b = ui.Button.text_button('send', padding=(20, 2), func=send_cmd)
    objects.append(b)
    
    b.rect.topleft = (20, 20)
    i.rect.midleft = b.rect.midright
    i.rect.x += 5
    
    t = ui.Textbox('connected', fgcolor=(0, 255, 0))
    t.rect.topright = (w - 20, 20)
    def check_conn():
        if Display.ac.connected and t.message != 'connected':
            t.set_fgcolor((0, 255, 0))
            t.set_message('connected')
        elif not Display.ac.connected and t.message != 'disconnected':
            t.set_fgcolor((255, 0, 0))
            t.set_message('disconnected')
    t.set_func(check_conn)
    objects.append(t)
    
    b = ui.Button.text_button('user', padding=(20, 2), func=Spec_Menu.build_and_run, args=[get_notification])
    b.rect.center = (w // 2, h // 2)
    objects.append(b)

    return objects

class Display(ui.Menu):
    ac = ac.Audio_Classifier()
    def __init__(self):
        self.thread = threading.Thread(target=Display.ac.run)
        super().__init__(get_objects=set_screen, args=[self])
        self.thread.start()

    def quit(self):
        self.ac.running = False
        self.thread.join()
        super().quit()
                    
    def update(self):
        #self.ac.record()
        super().update()
 
ui.init(size=(0, 0))#, flags=[pg.FULLSCREEN])
init()

d = Display()
try:
    d.run()
except SystemExit:
    pass
except:
    print(traceback.format_exc())
d.quit()




