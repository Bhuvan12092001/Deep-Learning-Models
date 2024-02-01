# -*- coding: utf-8 -*-
"""CS6910 DeepLearning - 1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17rb3KNBoOh-O5UpmivhhQWD-oKZfUovs

**Deep Learning Project - 1**

In this we are implementing Feed Forward Neural Network from scracth. \\
And using that on Fashion MNIST data set for classification with **GD,SGD,Batch-GD , Momentum, NAG , ADAGrad , RMSProp,ADAM**
"""

import numpy as np
from tqdm import tqdm

import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt

fashion_mnist = keras.datasets.fashion_mnist
(X_train, y_train), (X_test, y_test) = fashion_mnist.load_data()

#convert the vector of class indices into a matrix containing a one-hot vector for each instance
num_classes = 10
class_names = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
               "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]

# Sample dataset
class_labels =[]
n_rows = 1
n_cols = 10
plt.figure(figsize=(n_cols * 1.2, n_rows * 1.2))
index = 0
while (True):
  if y_train[index] not in class_labels:
    plt.subplot(n_rows, n_cols, len(class_labels)+1)
    plt.imshow(X_train[index], cmap="binary", interpolation="nearest")
    plt.axis('off')
    plt.title(class_names[y_train[index]], fontsize=12)
    class_labels.append(y_train[index])
  if(len(class_labels)==10):
    break
  index=index+1
plt.subplots_adjust(wspace=0.2, hspace=0.5)
plt.show()

#Split the full training set into a validation set and a (smaller) training set. 
#We also scale the pixel intensities down to the 0-1 range and convert them to floats, by dividing by 255.

X_train = X_train.reshape(X_train.shape[0], -1) / 255
X_test = X_test.reshape(X_test.shape[0], -1) / 255

y_train = np.eye(10)[y_train]
y_test = np.eye(10)[y_test]

class PCA:
    def __init__(self, n_components: int) -> None:
        self.n_components = n_components
        self.components = None
    
    def fit(self, X) -> None:
        # fit the PCA model
        cov_matrix = np.cov(X,rowvar=False)
        eignvals, eignvecs = np.linalg.eigh(cov_matrix)
        eignvecs = eignvecs[:, ::-1]
        self.components = eignvecs[:, :self.n_components]
        
    def transform(self, X) -> np.ndarray:
        # transform the data
        transformed_X = np.dot(X, self.components)
        return transformed_X

    def fit_transform(self, X) -> np.ndarray:
        # fit the model and transform the data
        self.fit(X)
        return self.transform(X)

from sklearn.preprocessing import StandardScaler
X_train = StandardScaler().fit_transform(X_train)
X_test = StandardScaler().fit_transform(X_test)

pca = PCA(n_components=100)
X_train = pca.fit_transform(X_train)
X_test = pca.transform(X_test)

class Layer:
  def __init__(self,num_of_inputs,num_of_neurons,activation):
    self.num_of_inputs = num_of_inputs
    self.num_of_neurons = num_of_neurons
    self.activations = activation
    np.random.seed(1234)
    self.W = np.random.randn(num_of_neurons,num_of_inputs)
    self.b = np.random.randn(num_of_neurons)

  def activation(self,input):
    if(self.activations=='ReLu'):
      return np.maximum(0,input)
    elif(self.activations=="sigmoid"):
      return 1/(1+np.exp(-input))
    elif(self.activations=="softmax"):
      max = np.max(input, axis = 1, keepdims=True)
      input -= max
      return(np.exp(input)/np.sum(np.exp(input), axis=1, keepdims=True))
    elif(self.activations=="tanh"):
      return np.tanh(input)
  
  def gradient_activation(self,input):
    if(self.activations=='ReLu'):
      return 1*(input>0)
    elif(self.activations=="sigmoid"):
      return (self.activation(input)*(1-self.activation(input)))
    elif(self.activations=="tanh"):
      return (1 - np.square(self.activation(input)))
  
  def forward(self,prev_H):
    bias = self.b.reshape(-1,1)
    self.A = np.dot(self.W,prev_H.T) + bias
    self.A = self.A.T
    self.H = self.activation(self.A)
    return self.H
  
  def backward(self,grad_A,prev_H,prev_A,gradient_activation):
    self.dW = np.dot(grad_A.T,prev_H)
    self.db = np.sum(grad_A, axis=0)
    grad_prev_H = np.dot(grad_A,self.W)
    derivative = gradient_activation(prev_A)
    grad_prev_A = grad_prev_H * derivative
    return grad_prev_A

from re import I
class Network:
  def __init__(self,num_of_inputs,num_of_hidden_layers,num_of_classes,num_of_neurons,activation):
    self.num_of_inputs = num_of_inputs
    self.num_of_hidden_layers = num_of_hidden_layers
    self.num_of_classes = num_of_classes
    self.num_of_neurons = num_of_neurons
    self.activation = activation
    self.Layers = []
    self.Layers.append(Layer(self.num_of_inputs,self.num_of_neurons,activation))
    for i in range(num_of_hidden_layers-1):
      self.Layers.append(Layer(self.num_of_neurons,self.num_of_neurons,"ReLu"))
    self.Layers.append(Layer(self.num_of_neurons,self.num_of_classes,"softmax"))
  
  def forward(self,inputs):
    self.inputs = inputs
    current_input = inputs
    for i in range(self.num_of_hidden_layers+1):
      current_ouput = self.Layers[i].forward(current_input)
      current_input = current_ouput
    self.y_pred = current_input
    return current_input
  
  def backward(self,outputs):
    grad_A = self.y_pred - outputs
    for i in range(self.num_of_hidden_layers, 0, -1):
      grad_A = self.Layers[i].backward(grad_A,self.Layers[i-1].H,self.Layers[i-1].A,self.Layers[i-1].gradient_activation)
    self.Layers[0].dW = np.dot(grad_A.T,self.inputs)
    self.Layers[0].db = np.sum(grad_A, axis=0)

  def miniBatchGrad(self,dW,db,learning_rate):
    for i in range(self.num_of_hidden_layers+1):
      self.Layers[i].W -= learning_rate*dW[i]
      self.Layers[i].b -= learning_rate*db[i]

  def momentumGrad(self,tW,tb,dW,db,learning_rate,momentum_rate):
    for i in range(self.num_of_hidden_layers+1):
      tW[i] = momentum_rate*tW[i] + learning_rate*dW[i]
      tb[i] = momentum_rate*tb[i] + learning_rate*db[i]
      self.Layers[i].W -= tW[i]
      self.Layers[i].b -= tb[i]
    return tW,tb
  
  def NAGrad(self,tW,tb,dW,db,learning_rate,momentum_rate):
    for i in range(self.num_of_hidden_layers+1):
      tW[i] = momentum_rate*tW[i] + dW[i]
      tb[i] = momentum_rate*tb[i] + db[i]
      self.Layers[i].W -= learning_rate*(momentum_rate*tW[i] + dW[i])
      self.Layers[i].b -= learning_rate*(momentum_rate*tb[i] + db[i])
    return tW,tb

  def AdaGrad(self,vW,vb,dW,db,learning_rate,epsilon=1e-8):
    for i in range(self.num_of_hidden_layers+1):
      vW[i] = vW[i] + dW[i]**2
      vb[i] = vb[i] + db[i]**2
      constantW = learning_rate / np.sqrt(vW[i] + epsilon)
      constantb = learning_rate / np.sqrt(vb[i] + epsilon)
      self.Layers[i].W -= constantW * dW[i]
      self.Layers[i].b -= constantb * db[i]
    return vW,vb

  def RmsProp(self,vW,vb,dW,db,learning_rate,epsilon=1e-8,beta = 0.9):
    for i in range(self.num_of_hidden_layers+1):
      vW[i] = beta*vW[i] + (1-beta)*dW[i]**2
      vb[i] = beta*vb[i] + (1-beta)*db[i]**2
      constantW = learning_rate / np.sqrt(vW[i] + epsilon)
      constantb = learning_rate / np.sqrt(vb[i] + epsilon)
      self.Layers[i].W -= constantW * dW[i]
      self.Layers[i].b -= constantb * db[i]
    return vW,vb
  
  def AdamGrad(self,vW,vb,tW,tb,dW,db,learning_rate,time,epsilon=1e-8,beta1=0.9 , beta2 = 0.999):
    for i in range(self.num_of_hidden_layers+1):
      tW[i] = beta1*tW[i] + (1-beta1)*dW[i]
      tb[i] = beta1*tb[i] + (1-beta1)*db[i]
      vW[i] = beta2*vW[i] + (1-beta2)*dW[i]**2
      vb[i] = beta2*vb[i] + (1-beta2)*db[i]**2
      tW_hat = tW[i]/(1-beta1**time)
      tb_hat = tb[i]/(1-beta1**time)
      vW_hat = vW[i]/(1-beta2**time)
      vb_hat = vb[i]/(1-beta2**time)
      self.Layers[i].W -= learning_rate*tW_hat/(np.sqrt(vW_hat)+epsilon)
      self.Layers[i].b -= learning_rate*tb_hat/(np.sqrt(vb_hat)+epsilon)
    return tW, tb, vW, vb           
    


  def crossEntropy(self, y_pred, y_true):
    return -np.sum(y_true*np.log(y_pred + 1e-9))/y_pred.shape[0]

  def test(self, X_test, y_test):
    self.forward(X_test)
    y_pred = self.Layers[-1].H
    loss = self.crossEntropy(y_pred, y_test)
    y_pred = np.argmax(y_pred, axis=1)
    y_test = np.argmax(y_test, axis=1)

    return round((np.sum(y_pred == y_test)/y_test.shape[0])*100,4), round(loss,4)

  
  def train(self,X_train,y_train,X_test,y_test,num_of_epochs,learning_rate,batch_size,opitimizer_fun,momentum_rate=0.9,epislon = 1e-08):
    train_accs= []
    train_losses= []
    test_accs = []
    test_losses = []
    epoch =1 
    while(epoch<=num_of_epochs):
      tW = [np.zeros_like(self.Layers[j].W) for j in range(self.num_of_hidden_layers+1)]
      tb = [np.zeros_like(self.Layers[j].b) for j in range(self.num_of_hidden_layers+1)]
      vW = [np.zeros_like(self.Layers[j].W) for j in range(self.num_of_hidden_layers+1)]
      vb = [np.zeros_like(self.Layers[j].b) for j in range(self.num_of_hidden_layers+1)]
      time = 1
      for i in tqdm(range(0, X_train.shape[0], batch_size)):   
        x = X_train[i:i+batch_size]
        y = y_train[i:i+batch_size]
        self.forward(x)
        self.backward(y)
        dW = [self.Layers[j].dW / X_train.shape[0] for j in range(self.num_of_hidden_layers+1)]
        db = [self.Layers[j].db / X_train.shape[0] for j in range(self.num_of_hidden_layers+1)]
        if(opitimizer_fun == "miniBatchGrad"):
          self.miniBatchGrad(dW, db, learning_rate)
        elif(opitimizer_fun == "momentumGrad"):
          tW,tb = self.momentumGrad(tW, tb,dW, db, learning_rate, momentum_rate)
        elif(opitimizer_fun == "NAGrad"):
          tW,tb = self.NAGrad(tW, tb,dW, db,learning_rate, momentum_rate)
        elif(opitimizer_fun =="AdaGrad"):
          vW,vb = self.AdaGrad(vW,vb,dW,db,learning_rate)
        elif(opitimizer_fun =="RmsProp"):
          vW,vb = self.RmsProp(vW,vb,dW,db,learning_rate)
        elif(opitimizer_fun =="AdamGrad"):
          tW,tb,vW,vb = self.AdamGrad(vW,vb,tW,tb,dW,db,learning_rate,time)
        time=time+1
      train_acc, train_loss = self.test(X_train, y_train)
      test_acc, test_loss = self.test(X_test, y_test)
      train_accs.append(train_acc)
      train_losses.append(train_loss)
      test_accs.append(test_acc)
      test_losses.append(test_loss)
      print(f"Epoch : {epoch}  train_acc : {train_acc} train_loss : {train_loss} test_acc : {test_acc} test_loss : {test_loss}")
      epoch = epoch+1
      if(epoch%3==0):
        learning_rate = learning_rate/2
    return train_accs,train_losses,test_accs,test_losses

num_of_inputs=100
num_of_hidden_layers= 4
num_of_classes = 10
num_of_neurons = 128
activation = "sigmoid"
nn = Network(num_of_inputs,num_of_hidden_layers,num_of_classes,num_of_neurons,activation)
num_of_epochs= 20
learning_rate = 1e-2
batch_size = 32
opitimizer_fun = "miniBatchGrad"
train_accs1,train_losses1,test_accs1,test_losses1=nn.train(X_train,y_train,X_test,y_test,num_of_epochs,learning_rate,batch_size,opitimizer_fun)

num_of_inputs=100
num_of_hidden_layers= 4
num_of_classes = 10
num_of_neurons = 128
activation = "sigmoid"
nn = Network(num_of_inputs,num_of_hidden_layers,num_of_classes,num_of_neurons,activation)
num_of_epochs= 20
learning_rate = 1e-2
batch_size = 32
opitimizer_fun = "momentumGrad"
train_accs2,train_losses2,test_accs2,test_losses2=nn.train(X_train,y_train,X_test,y_test,num_of_epochs,learning_rate,batch_size,opitimizer_fun)

num_of_inputs=100
num_of_hidden_layers= 4
num_of_classes = 10
num_of_neurons = 128
activation = "sigmoid"
nn = Network(num_of_inputs,num_of_hidden_layers,num_of_classes,num_of_neurons,activation)
num_of_epochs= 20
learning_rate = 1e-2
batch_size = 32
opitimizer_fun = "AdaGrad"
train_accs3,train_losses3,test_accs3,test_losses3=nn.train(X_train,y_train,X_test,y_test,num_of_epochs,learning_rate,batch_size,opitimizer_fun)

num_of_inputs=100
num_of_hidden_layers= 4
num_of_classes = 10
num_of_neurons = 128
activation = "sigmoid"
nn = Network(num_of_inputs,num_of_hidden_layers,num_of_classes,num_of_neurons,activation)
num_of_epochs= 20
learning_rate = 1e-2
batch_size = 32
opitimizer_fun = "RmsProp"
train_accs4,train_losses4,test_accs4,test_losses4=nn.train(X_train,y_train,X_test,y_test,num_of_epochs,learning_rate,batch_size,opitimizer_fun)

num_of_inputs=100
num_of_hidden_layers= 4
num_of_classes = 10
num_of_neurons = 128
activation = "sigmoid"
nn = Network(num_of_inputs,num_of_hidden_layers,num_of_classes,num_of_neurons,activation)
num_of_epochs=  20
learning_rate = 1e-2
batch_size = 32
opitimizer_fun = "AdamGrad"
train_accs5,train_losses5,test_accs5,test_losses5=nn.train(X_train,y_train,X_test,y_test,num_of_epochs,learning_rate,batch_size,opitimizer_fun)

#Results Plotting
import matplotlib.pyplot as plt
figure, axis = plt.subplots(2, 2,figsize=(15, 12.5))

train_accs5,train_losses5,test_accs5,test_losses5

epochs = [ i for i in range(1,21)]

axis[0,0].set_title("Training Loss",fontsize=20,color="green")
axis[0,0].set_xlabel("#Epochs")
axis[0,0].set_ylabel("Loss")
axis[0,0].plot(epochs,train_losses1,label="MiniBatchSGD")
axis[0,0].plot(epochs,train_losses2,label="Momentum")
axis[0,0].plot(epochs,train_losses3,label="ADAGrad")
axis[0,0].plot(epochs,train_losses4,label="RMSProp")
axis[0,0].plot(epochs,train_losses5,label="ADAMGrad")
axis[0,0].legend()


axis[0,1].set_title("Testing Loss",fontsize=20,color="green")
axis[0,1].set_xlabel("#Epochs")
axis[0,1].set_ylabel("Loss")
axis[0,1].plot(epochs,test_losses1,label="MiniBatchSGD")
axis[0,1].plot(epochs,test_losses2,label="Momentum")
axis[0,1].plot(epochs,test_losses3,label="ADAGrad")
axis[0,1].plot(epochs,test_losses4,label="RMSProp")
axis[0,1].plot(epochs,test_losses5,label="ADAMGrad")
axis[0,1].legend()

axis[1,0].set_title("Training Accuracy",fontsize=20,color="green")
axis[1,0].set_xlabel("#Epochs")
axis[1,0].set_ylabel("Accuracy")
axis[1,0].plot(epochs,train_accs1,label="MiniBatchSGD")
axis[1,0].plot(epochs,train_accs2,label="Momentum")
axis[1,0].plot(epochs,train_accs3,label="ADAGrad")
axis[1,0].plot(epochs,train_accs4,label="RMSProp")
axis[1,0].plot(epochs,train_accs5,label="ADAMGrad")
axis[1,0].legend()

axis[1,1].set_title("Testing Accuracy",fontsize=20,color="green")
axis[1,1].set_xlabel("#Epochs")
axis[1,1].set_ylabel("Accuracy")
axis[1,1].plot(epochs,test_accs1,label="MiniBatchSGD")
axis[1,1].plot(epochs,test_accs2,label="Momentum")
axis[1,1].plot(epochs,test_accs3,label="ADAGrad")
axis[1,1].plot(epochs,test_accs4,label="RMSProp")
axis[1,1].plot(epochs,test_accs5,label="ADAMGrad")
axis[1,1].legend()
