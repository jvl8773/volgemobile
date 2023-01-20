import numpy as np
import pyaudio
import time
import librosa
from librosa import display
from matplotlib import pyplot as plt
from queue import Queue


class AudioHandler(object):
    def __init__(self):
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 22050
        self.CHUNK = int(self.RATE / 1)
        self.num_chunks = 4
        self.p = None
        self.stream = None
        self.cache: list[np.ndarray] = []
        self.count: int = 0

    def start(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input=True,
                                  output=False,
                                  stream_callback=self.callback,
                                  frames_per_buffer=self.CHUNK)

    def stop(self):
        self.stream.close()
        self.p.terminate()

    def callback(self, in_data, frame_count, time_info, flag):
        self.count += 1

        numpy_array = np.frombuffer(in_data, dtype=np.float32)

        self.cache.append(numpy_array)

        print(len(self.cache))

        if len(self.cache) < self.num_chunks:
            return None, pyaudio.paContinue

        print("removing item from cache")
        self.cache.pop(0)

        arr = np.concatenate(self.cache)

        n_fft = 2048
        hop_length = 512

        # Normalize between -1 and 1
        normalized_y = librosa.util.normalize(arr)

        # Compute STFT
        stft = librosa.core.stft(normalized_y, n_fft=n_fft, hop_length=hop_length)

        n_mels = 128

        # Generate mel scaled spectrogram
        mel = librosa.feature.melspectrogram(S=stft, n_mels=n_mels)

        # Convert sound intensity to log amplitude:
        mel_db = librosa.amplitude_to_db(abs(mel))

        # Normalize between -1 and 1
        normalized_mel = librosa.util.normalize(mel_db)

        # Plot spectrogram from STFT
        if self.count % 2 == 0:
            plt.figure(figsize=(12, 4))
            librosa.display.specshow(mel_db, x_axis='time', y_axis='mel')
            plt.colorbar(format='%+2.0f dB')
            plt.title('MEL-Scaled Spectrogram')
            plt.tight_layout()
            plt.show()

        # n_mels = 128
        #
        # mel = librosa.feature.melspectrogram(S=stft, n_mels=n_mels)
        return None, pyaudio.paContinue

    def mainloop(self):
        while (self.stream.is_active()): # if using button you can set self.stream to 0 (self.stream = 0), otherwise you can use a stop condition
            time.sleep(2.0)


audio = AudioHandler()
audio.start()     # open the the stream
audio.mainloop()  # main operations with librosa
audio.stop()