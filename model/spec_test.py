import os
import tensorflow as tf
import librosa
import numpy as np
import cv2
import random

lookup = (
    'air_conditioner', 
      'car_horn', 
      'children_playing', 
      'dog bark', 
      'drilling', 
      'engine_idling', 
      'gun_shot', 
      'jackhammer', 
      'siren', 
      'street_music'
)

model = tf.keras.models.load_model('saved_model/model')

def get_test_images(num):
    images = []
    files = [f'img/{fold}/{f}' for fold in os.listdir('img') for f in os.listdir(f'img/{fold}')]
    random.shuffle(files)
    images = {f: f.split('/')[-1].split('-')[0] for f in files[:num]}
    return images
  
num = 500
images = get_test_images(num)
  
correct = 0
for img, cls in images.items():
    img = tf.keras.utils.load_img(img, target_size=(49, 49))
    img_array = tf.keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)
    
    predict_x = model.predict(img_array) 
    classes_x = np.argmax(predict_x, axis=1)
    p = lookup[classes_x[0]]
    c = cls
    if p == c:
        correct += 1
        
print(f'{correct}/{num} correct guesses\naccuracy: {(correct / num) * 100}%')

