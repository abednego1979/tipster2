# -*- coding: utf-8 -*-

#Python 3.5.x

import datetime

from tensorflow.examples.tutorials.mnist import input_data

mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)

print (mnist.train.images.shape, mnist.train.labels.shape)
print (mnist.test.images.shape, mnist.test.labels.shape)
print (mnist.validation.images.shape, mnist.validation.labels.shape)

begin = datetime.datetime.now()
import tensorflow as tf
sess = tf.InteractiveSession()
#input images data through x
x = tf.placeholder(tf.float32, [None, 784])

W = tf.Variable(tf.zeros([784,10]))
b = tf.Variable(tf.zeros([10]))

#y = softmax(Wx+b), y is the estimated value
y = tf.nn.softmax(tf.matmul(x, W) + b)

#input labels data through y_
y_ = tf.placeholder(tf.float32, [None, 10])
cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))

#define the optimization function
train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)

#
tf.global_variables_initializer().run()

#run
for i in range(1000):
    batch_xs, batch_ys = mnist.train.next_batch(100)
    train_step.run({x: batch_xs, y_: batch_ys})

#train over, 
correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))

accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

print (accuracy.eval({x: mnist.test.images, y_: mnist.test.labels}))
end = datetime.datetime.now()
print((end-begin))