import os
import sys
import math
import struct
import wave
import threading
import subprocess

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import paramiko
import tensorflow as tf
import librosa
import librosa.display
import numpy as np
import pyaudio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import base
from network import Network

def init():
    if not os.path.exists('running_data'):
        os.mkdir('running_data')

class Mic:
    MODEL = tf.keras.models.load_model('saved_model/model')
    LOOKUP = (
        #'air_conditioner', #r
        'car_horn', 
        #'children_playing', #r
        'dog_bark', 
        #'drilling', #r
        #'engine_idling', #r
        'gun_shot',
        #'jackhammer', #r
        'siren', 
        #'street_music', #r
        'None'
    )
    SCALES = (1, 0.3, 1, 1.5, 1, 1, 1, 1, 1, 1)
    
    SHORT_NORMALIZE = 1 / 32768
    FORMAT = pyaudio.paInt16
    WIDTH = pyaudio.get_sample_size(FORMAT)
    CHANNELS = 1
    SAMPLE_RATE = 44100
    RESAMPLE_RATE = 22050
    FRAMES_PER_BUFFER = 512 * 2
    SECONDS = 2.5
    T = int((SAMPLE_RATE / FRAMES_PER_BUFFER) * SECONDS)
    THRESH = 7
    
    @classmethod
    def get_predictions(cls, img_array):
        predict_x = cls.MODEL.predict(img_array)[0].tolist()
        predictions = {cls.LOOKUP[i]: p for i, p in enumerate(predict_x)}
        predictions['None'] = 0
        return predictions
    
    def __init__(self, name, index, quad):
        self.recording = True
        
        self.name = name
        self.index = index
        self.quad = quad
        
        self.snd_path = f'running_data/{self.name}-{self.index}.wav'
        self.img_path = f'running_data/{self.name}-{self.index}.png'
        
        self.frames = []
        self.stream = Audio_Classifier.p.open(
            format=Mic.FORMAT,
            channels=Mic.CHANNELS,
            rate=Mic.SAMPLE_RATE, 
            frames_per_buffer=Mic.FRAMES_PER_BUFFER,
            input=True,
            input_device_index=self.index
        )
        
        self.amplitude = 0
        self.prediction = 'None'
        self.hist = []
        self.confidence = 0
        
    def set_quad(self, quad):
        self.quad = quad
        
    def set_recording(self, recording):
        self.recording = recording
        if not recording:
            self.amplitude = 0
            self.prediction = 'None'

    def get_amplitude(self):
        if not self.frames:
            return 0
        block = b''.join(self.frames)
        count = len(block) // 2
        format = f'{count}h'
        shorts = struct.unpack(format, block)

        sum_squares = 0
        for sample in shorts:
            n = sample * Mic.SHORT_NORMALIZE
            sum_squares += n * n
            
        amplitude = math.sqrt(sum_squares / count)
        return amplitude
        
    def set_amplitude(self):
        self.amplitude = self.get_amplitude()

    def get_prediction(self):
        img = tf.keras.utils.load_img(self.img_path, target_size=(50, 50))
        img_array = tf.keras.utils.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0)
        predictions = Mic.get_predictions(img_array)

        prediction = max(predictions, key=predictions.get)
        confidence = predictions[prediction]
        if confidence < Mic.THRESH:
            prediction = 'None'

        return (confidence, prediction)
        
    def set_prediction(self):
        c, p = self.get_prediction()
        self.confidence = c
        self.prediction = p
 
    def record(self):
        self.stream.start_stream()
        for _ in range(Mic.T):
            data = self.stream.read(Mic.FRAMES_PER_BUFFER)
            self.frames.append(data)
            if not self.recording:
                break
                
        self.stream.stop_stream()
        self.write_wav()
        
    def write_wav(self):
        data = b''.join(self.frames)
        sound_file = wave.open(self.snd_path, 'wb')
        sound_file.setnchannels(Mic.CHANNELS)
        sound_file.setsampwidth(Mic.WIDTH)
        sound_file.setframerate(Mic.SAMPLE_RATE)
        sound_file.writeframes(data)
        sound_file.close()
        
    def plot_hist(self):
        fig = plt.figure(0, figsize=base.img_size, dpi=base.dpi)
        ax = fig.add_subplot(111)
        ax.set_frame_on(False)

        audio, sr = librosa.load(self.snd_path, res_type='kaiser_fast')
        audio = librosa.resample(audio, sr, Mic.RESAMPLE_RATE)
        #audio, _ = librosa.effects.trim(audio, frame_length=8000, top_db=80)
        S = librosa.feature.melspectrogram(y=audio, sr=Mic.RESAMPLE_RATE)
        librosa.display.specshow(librosa.power_to_db(S, ref=np.max))
        
        plt.savefig(self.img_path, dpi=base.dpi, bbox_inches='tight', pad_inches=0)
        plt.clf()
            
    def update_data(self):
        self.plot_hist()
        self.set_amplitude()
        self.set_prediction()
        self.frames.clear()
 
    def close(self):
        self.stream.stop_stream()
        self.stream.close()

class Audio_Classifier(Network):   
    p = pyaudio.PyAudio()
    banned = ['Mapper']#, 'Array']
    quads = ('fl', 'fr', 'bl', 'br')
    
    eth0 = '169.254.95.67'
    username = 'pi'
    password = 'raspberry'
    directory = 'Desktop/controller'
    
    server = '169.254.95.67'#'169.254.49.112'
    port = 5555
    
    @classmethod
    def get_devices(cls):
        devices = []
        
        info = cls.p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(numdevices):
            device = cls.p.get_device_info_by_host_api_device_index(0, i)
            name = device.get('name')
            max_channels = device.get('maxInputChannels')
            if max_channels > 0 and not any({banned in name for banned in cls.banned}):
                devices.append((name, i))
                
        return devices[::-1]
    
    def __init__(self, mode=1):
        self.args = sys.argv.copy()
        self.running = True
        Network.__init__(self, Audio_Classifier.server, Audio_Classifier.port, mode, timeout=10)

        self.mics = []
        self.threads = []

        devices = Audio_Classifier.get_devices()
        for j, (name, i) in enumerate(devices):
            quad = Audio_Classifier.quads[j]
            mic = Mic(name, i, quad)
            self.mics.append(mic)
            
        if self.mics:
            self.start_connection()
        else:
            print('no recording devices found')
            
    @property
    def activated_mics(self):
        cmd = self.get_cmd()
        quads = cmd[1:].split()[0].split(',')
        mics = []
        for q in quads:
            m = self.get_mic_by_quad(q)
            if m:
                mics.append(m)
        return mics
            
    def start_connection(self):
        ssh_connected = False

        dir = Audio_Classifier.directory

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(Audio_Classifier.eth0, username=Audio_Classifier.username, password=Audio_Classifier.password, timeout=5)
            ssh_connected = True
            print('ssh connected')
        except Exception as e:
            print('error while connecting')
            
        if ssh_connected:
            mode = self.mode ^ 1
            cmd = f'cd {dir};python controller.py {self.server} {self.port} {mode}'
            stdin, stdout, stderr = ssh.exec_command(cmd)
        ssh.close()
        
        if ssh_connected:
            self.start_network()
                
    def get_cmd(self):
        cmd = ''

        max_mic = None
        for m in self.mics:
            if m.amplitude > getattr(max_mic, 'amplitude', 0) and m.prediction != 'None':
                max_mic = m
            
        if max_mic:
        
            for m in self.mics:
                a = (m.amplitude / max_mic.amplitude) * 100
                if a > 75 and m.prediction == max_mic.prediction:
                    cmd += f'{m.quad},'
                    
        if cmd:
            cmd = cmd[:-1] + ' x1'
        else:
            cmd = 'a 0'
        cmd = '-' + cmd
        
        return cmd

    def get_mic(self, i):
        if i < len(self.mics):
            return self.mics[i]
            
    def get_mic_by_quad(self, quad):
        for m in self.mics:
            if m.quad == quad:
                return m
                
    def show_info(self):
        for m in self.mics:
            print(m.prediction, m.confidence)
            
    def update_motors(self):
        for m in self.mics:
            if m.recording:
                m.set_amplitude()
                
        if 'd' in self.args:
            return
            
        cmd = self.get_cmd()
        if cmd:
            self.send(cmd)
            self.recv()
            
    def stop_mics(self):
        for m in self.mics:
            m.set_recording(False)
        for t in self.threads:
            t.join()

    def record(self):
        for m in self.mics:
            if m.recording:
                t = threading.Thread(target=m.record)
                self.threads.append(t)
                t.start()  
 
        while any({t.is_alive() for t in self.threads}):
            self.update_motors()
            if not self.running:
                self.stop_mics()
        self.threads.clear()
            
        for m in self.mics:
            if m.recording:
                m.update_data()

    def run(self):
        while self.running and self.mics:
            try:
                self.record()
            except KeyboardInterrupt:
                break
        self.close()

    def close(self):
        for m in self.mics:
            m.set_recording(False)
        for t in self.threads:
            t.join()
        for m in self.mics:
            m.close() 
        Audio_Classifier.p.terminate()
        
        super().close()
            
init()
if __name__ == '__main__':   
    ac = Audio_Classifier()
    ac.run()

