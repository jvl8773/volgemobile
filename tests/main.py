import os
import math
import struct
import wave

import numpy as np
import pyaudio

SHORT_NORMALIZE = 1 / 32768
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 44100
FRAMES_PER_BUFFER = 512 * 2
SECONDS = 5
T = int((SAMPLE_RATE / FRAMES_PER_BUFFER) * SECONDS)

mic = None
p = pyaudio.PyAudio()

info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(numdevices):
    device = p.get_device_info_by_host_api_device_index(0, i)
    name = device.get('name')
    max_channels = device.get('maxInputChannels')
    if max_channels > 0 and 'PnP' in name:
        print(name, max_channels)
        break
        
raw_data = b''
        
stream = p.open(
            format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, 
            frames_per_buffer=FRAMES_PER_BUFFER, input=True, input_device_index=i
        )
stream.start_stream()
for _ in range(T):
    d = stream.read(FRAMES_PER_BUFFER)
    raw_data += d
stream.stop_stream() 
p.terminate()   

data = np.frombuffer(raw_data, np.int16)
print(data)

sound_file = wave.open('test.wav', 'wb')
sound_file.setnchannels(CHANNELS)
sound_file.setsampwidth(pyaudio.get_sample_size(FORMAT))
sound_file.setframerate(SAMPLE_RATE)
sound_file.writeframes(raw_data)
sound_file.close()
        
        
        



