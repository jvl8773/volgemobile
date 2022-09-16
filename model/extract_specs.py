import os
import csv
import random

import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import base

def make_dirs():
    if not os.path.exists(base.img_fold):
        os.mkdir(base.img_fold)
        
    folds = os.listdir(base.img_fold)
    for i in range(10):
        if str(i) not in folds and i in base.accepted:
            os.mkdir(f'{base.img_fold}/{i}')

def save_images():
    make_dirs()
    
    audio_dataset_path = 'UrbanSound8K/audio'
    with open('UrbanSound8K/metadata/UrbanSound8K.csv', 'r') as f:
        metadata = list(csv.DictReader(f))

    plt.margins(0)              
    fig = plt.figure(figsize=base.img_size, dpi=base.dpi)
    ax = fig.add_subplot(111)
    ax.set_frame_on(False)

    i = 1
    num = len(metadata)
    max_length = max({round(float(row['end'])) - round(float(row['start'])) for row in metadata})

    for row in metadata:
        id = int(row['classID'])
        if id not in base.accepted:
            continue
            
        print(f'extracting image {i} of {num}')
        file = os.path.join(os.path.abspath(audio_dataset_path), f"fold{row['fold']}/", row['slice_file_name'])

        fig = plt.figure(0, figsize=base.img_size, dpi=base.dpi)
        ax = fig.add_subplot(111)
        ax.set_frame_on(False)
    
        audio, sr = librosa.load(file, sr=44100, res_type='kaiser_fast')
        target_length = max_length * sr
        #audio = librosa.util.fix_length(audio, size=target_length)
        S = librosa.feature.melspectrogram(y=audio, sr=sr)
        librosa.display.specshow(librosa.power_to_db(S, ref=np.max))
    
        plt.savefig(f"{base.img_fold}/{id}/{row['class']}-{i}.png", dpi=base.dpi, bbox_inches='tight', pad_inches=0)
        plt.clf()
    
        i += 1
        
def normalize_folders():
    abs_dir = os.getcwd()
    folds = os.listdir(base.img_fold)
    min_imgs = min({len(os.listdir(f'{base.img_fold}/{dir}')) for dir in folds})
    for fold in folds:
        dir = f'{base.img_fold}/{fold}'
        imgs = os.listdir(dir)
        while len(imgs) > min_imgs:
            file = random.choice(imgs)
            path = f'{dir}/{file}'
            os.remove(path)
            imgs.remove(file)
    
save_images()
normalize_folders() 