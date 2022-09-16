import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D, Rescaling

import base

batch_size = 40
classes = len(base.accepted)

train_ds = tf.keras.utils.image_dataset_from_directory(
    base.img_fold,
    validation_split=0.2,
    subset='training',
    seed=123,
    image_size=base.img_size,
    batch_size=batch_size
)
    
val_ds = tf.keras.utils.image_dataset_from_directory(
    base.img_fold,
    validation_split=0.2,
    subset='validation',
    seed=123,
    image_size=base.img_size,
    batch_size=batch_size
)

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

model = Sequential()

model.add(Rescaling(1./255, input_shape=(base.img_height, base.img_width, 3)))
model.add(Conv2D(32, 3, padding='same', activation='relu'))
model.add(Conv2D(64, 3, padding='same', activation='relu'))
model.add(MaxPooling2D())
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(classes))

learning_rate = 0.001

loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
opt = tf.keras.optimizers.Adam(learning_rate=learning_rate)

model.compile(opt, loss_fn, metrics=['accuracy'])
model.summary()

epochs = 30
history = model.fit(train_ds, validation_data=val_ds, epochs=epochs)
model.save('saved_model/model')





