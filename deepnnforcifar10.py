# -*- coding: utf-8 -*-
"""DeepNNforCIFAR10.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12SYKJ5JmGtahfEMQ_YYBVkDwck0fvB7Z

# Deep neural nets for object recognition
In this exercise, you will first develop a fully connected neural net model and test it on the CIFAR-10 problem. Then, you will build a convolutional neural net model and test it on the same CIFAR-10 problem. The purpose of this exercise is to give you a working understanding of neural net models and give you experience in tuning their (many) hyper-parameters.
"""

import torch
import torchvision
import torchvision.transforms as transforms
import numpy as np
import matplotlib.pyplot as plt
import torch.nn as nn

import sklearn
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import copy

"""# The CIFAR10 dataset
- Download and normalize the CIFAR10 dataset from torchvision
- Split the CIFAR10 data into train, validation and test set
- Set the batch size for processing these datasets
- Build the dataloaders for train, validation, and test set which will be used in the training loop
- Define the string class labels (targets are numeric 0-9)
"""

# mean and std for the RGB channels in CIFAR10
tmean = [0.49139968, 0.48215841, 0.44653091]
tstd = [0.24703223, 0.24348513, 0.26158784]

# transform the 32x32x3 images into a tensor after normalizing
# each channel using the parameters above
transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize(tmean, tstd)])

# download and transform the  trainset and testset for training
trainset = torchvision.datasets.CIFAR10(root='./data',train=True,download=True,transform=transform)
testset = torchvision.datasets.CIFAR10(root='./data',train=False,download=True,transform=transform)

#split trainset into a train and a val set (90-10 split)
lengths = [int(p * len(trainset)) for p in [0.9,0.1]]
tr,v = torch.utils.data.random_split(trainset,lengths)
train_sampler = torch.utils.data.SubsetRandomSampler(tr.indices)
val_sampler = torch.utils.data.SubsetRandomSampler(v.indices)

# set batch size and set up the data generators for train, val, test sets
batch_size = 64
trainloader = torch.utils.data.DataLoader(trainset,batch_size=batch_size,sampler=train_sampler)
valloader = torch.utils.data.DataLoader(trainset,batch_size=batch_size,sampler=val_sampler)
testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size)

print("Number of training batches = ",len(trainloader))
print("Number of validation batches = ",len(valloader))
print("Number of test batches = ",len(testloader))

# define the output classes
classes = ('plane', 'car', 'bird', 'cat',
           'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

"""# Visualize the training data"""

Xtr,ytr = next(iter(trainloader))
# make a 8x8 grid and display 64 images from the first batch of training data
rows,cols = 8,8
fig = plt.figure(figsize=(8,8),constrained_layout=True)

for i in range(0,rows*cols):
    fig.add_subplot(rows,cols,i+1)
    tmp = np.transpose(Xtr[i].numpy(),(1,2,0))
    plt.imshow(((tmp*tstd + tmean)*255).astype(np.uint8))
    plt.xticks([])
    plt.yticks([])
    plt.title(classes[ytr[i].numpy()])

"""# A five layer fully connected (FC) feedforward network
- has an input layer, two hidden layers, and an output layer
- complete the function definitions below
- you will find d2l.ai Chapters 5.2, 5.6, 6.1, 6.2, 6.3 very useful
"""

import torch.nn.functional as F

class FiveLayerFC(nn.Module):

    def __init__(self, input_size, hidden_size1, hidden_size2, num_classes, lr, wd):
        super(FiveLayerFC, self).__init__()
        self.lr = lr
        self.wd = wd

        # Set up the network structure using nn.Sequential
        self.net = nn.Sequential(
            nn.Flatten(),  # Flatten the input
            nn.Linear(input_size, hidden_size1),
            nn.ReLU(),     # ReLU activation after the first hidden layer
            nn.Linear(hidden_size1, hidden_size2),
            nn.ReLU(),     # ReLU activation after the second hidden layer
            nn.Linear(hidden_size2, num_classes)
        )

        # Xavier normal initialization for weights in the hidden layers
        for layer in [1, 3]:
            nn.init.xavier_normal_(self.net[layer].weight)

        # Zero initialization for bias weights
        for layer in [1, 3, 5]:
            nn.init.zeros_(self.net[layer].bias)
        self.configure_optimizers()

    def forward(self, x):
        # Forward propagate the input x through the network
        return self.net(x)

    def loss(self,yhat,y,averaged=True):
        # use nn.functional.cross_entropy() to evaluate loss with prediction (yhat)
        # and truth (y). Average it over a batch.
        # YOUR CODE HERE

        return nn.functional.cross_entropy(yhat, y, reduction='mean')


    def predict(self, x):
        # Propagate x forward and return the index of the highest valued output component
        with torch.no_grad():
            outputs = self.forward(x)
            _, predicted = torch.max(outputs, 1)
        return predicted

    def configure_optimizers(self):
        # Set up the Adam optimizer with learning rate and weight decay specified
        #optimizer = torch.optim.Adam(self.parameters(), lr=self.lr, weight_decay=self.wd)
        self.optimizer = torch.optim.Adam(self.parameters(), lr = self.lr, weight_decay = self.wd)
        #return optimizer

"""# Test the FiveLayerFC class
- set the device to GPU if you have access to it.
- In Google Colab, you can select runtime, and pick the free T4 GPU choice.
- to understand how GPU memory and CPU memory interact, read Section 6.7 of the d2l.ai textbook.
"""

lr = 1e-2
wd = 1e-2

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print('Device is: ', device)

def test_FiveLayerFC(lr,wd):
    input_size = 32*32*3
    x = torch.zeros((64, input_size), dtype=torch.float).to(device)  # minibatch size 64, feature dimension 50
    model = FiveLayerFC(input_size, 100, 100,10,lr,wd).to(device)
    outputs = model(x)
    print(outputs.size())  # you should see [64, 10]

test_FiveLayerFC(lr,wd)

"""# Checking the network setup
As a sanity check, make sure you can overfit a small dataset of 64 images. We will use a five-layer network with 100 units in the two hidden layers. You will need to tweak the learning rate and weight decay, but you should be able to overfit and achieve 100% training accuracy within 20 epochs. We have given you parameter choices that work. You should report on at least another choice of learning rate and weight decay that allows you to fit the training data to 100% accuracy within 20 epochs.

Complete the function train_model_small that takes a single batch (Xtr,ytr) of 64 images and their labels for training, and a single batch (Xval,yval) of validation images and trains an initialized model for num_epochs epochs.

- Initialize train_loss and val_loss (which will hold training and validation set loss for each epoch)
- Configure optimizer for the model
- for epoch in range(num_epochs)
    - zero out gradients in the optimizer
    - compute output of network by forward propagating Xtr through network
    - compute loss using output and ytr
    - backpropagate the loss
    - store the training loss for this epoch
    - compute validation set loss for this epoch (remember to turn off gradient update with torch.no_grad())
- return model, train_loss and val_loss

"""

Xtr,ytr = next(iter(trainloader))
Xval, yval = next(iter(valloader))
num_epochs = 20

lr = 1e-2
wd = 1e-3


def train_model_small(model,Xtr,ytr,Xval,yval,num_epochs):

    # YOUR CODE HERE
    train_loss, val_loss = [], []
    for e in range(num_epochs):
        # Zero out the gradients
        model.optimizer.zero_grad()

        # Forward prop
        yhat = model(Xtr)
        loss = model.loss(yhat,ytr)

        # Backward prop
        loss.backward()
        model.optimizer.step()

        # Tracking training loss
        train_loss.append(loss.item())

        # Tracking validation loss
        with torch.no_grad():
            yhat_val = model(Xval)
            val_loss.append(model.loss(yhat_val, yval).item())

    return model, train_loss, val_loss
    # END YOUR CODE

def plot_losses(train_loss, val_loss, num_epochs, title):
    plt.plot(range(num_epochs),train_loss,label="Training Loss")
    plt.plot(range(num_epochs),val_loss,label="Validation Loss")
    plt.title(title)
    plt.legend()
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.grid()
    plt.xticks(range(num_epochs))
    plt.show()

model = FiveLayerFC(32*32*3,100,100,10,lr,wd)
model,train_loss,val_loss = train_model_small(model,Xtr,ytr,Xval,yval,num_epochs)

plot_losses(train_loss, val_loss, num_epochs, "Loss vs Epochs")

"""# Test your model on the training set
- you should get 100% accuracy
"""

with torch.no_grad():
    ypred = model.predict(Xtr)

    cm = sklearn.metrics.confusion_matrix(ytr,ypred)
    acc = sklearn.metrics.accuracy_score(ytr,ypred)
    print('Accuracy on test set = ',acc)
    print(cm)
    print(sklearn.metrics.classification_report(ytr,ypred))

"""# Train the full model
- Initialize train_loss and val_loss (which will hold training and validation set loss for each epoch)
- Configure optimizer for the model
- for epoch in range(num_epochs)
    - for each batch (Xtr,ytr) in training set
       - zero out gradients in the optimizer
       - compute output of network by forward propagating Xtr through network
       - compute loss using output and ytr
       - backpropagate the loss
       - accumulate the training loss for this batch
    - store training loss for this epoch
    - compute validation set loss for this epoch (remember to turn off gradient update with torch.no_grad()) and remember to iterate over all the batches of the validation set
    
- return model, train_loss and val_loss

"""

from tqdm.notebook import tqdm
def train_model(model,trainloader,valloader,num_epochs):
    # YOUR CODE HERE
    train_loss, val_loss = [0]*num_epochs, [0]*num_epochs
    train_len = len(trainloader)
    val_len = len(valloader)

    for i in tqdm(range(num_epochs)):
        for Xtr, ytr in trainloader:
            Xtr, ytr = Xtr.to(device), ytr.to(device)
            model.optimizer.zero_grad()

            yhat = model(Xtr)
            loss = model.loss(yhat, ytr)

            loss.backward()
            model.optimizer.step()

            train_loss[i] += loss.item()

        with torch.no_grad():
            for Xval, yval in valloader:
                Xval, yval = Xval.to(device), yval.to(device)
                yhat = model(Xval)
                val_loss[i] += model.loss(yhat, yval).item()

        train_loss[i] /= train_len
        val_loss[i] /= val_len

    return model, train_loss, val_loss
    # END YOUR CODE

"""# Train and test performance of model
- hyperparameter choice: lr = 1e-5, weight_decay = 1e-2
- train the model using training and validation data
- get accuracy, confusion matrix and classification report on test data

"""

lr = 1e-5
wd = 1e-2
num_epochs = 20

model = FiveLayerFC(32*32*3,200,200,10,lr,wd).to(device)
model,train_loss,val_loss = train_model(model,trainloader,valloader,num_epochs)

plt.plot(torch.arange(num_epochs),train_loss, label="train_loss")
plt.plot(torch.arange(num_epochs),val_loss, label="val_loss")
plt.legend()

def model_eval(model,testloader):
    with torch.no_grad():
        ys=[]
        outputs=[]
        for i, tdata in enumerate(testloader):
            tX,ty = tdata
            tX=tX.to(device)
            ty=ty.to(device)
            output = model.predict(tX)
            ys.append(ty.detach().cpu().numpy())
            outputs.append(output.detach().cpu().numpy())


    ys=np.hstack(ys)
    outputs= np.hstack(outputs)
    cm = sklearn.metrics.confusion_matrix(ys,outputs)
    print("****************************************************************************************")
    print("confusion matrix:")
    print(cm)

    print("****************************************************************************************")
    print("performance matrix:")
    print(sklearn.metrics.classification_report(ys,outputs))

model_eval(model,testloader)

"""# Train and test performance of model
- hyperparameter choice: lr = 5e-6, weight_decay = 5e-2, num_epochs  = 30
- build the model by calling the train_model function
- plot the training and validation loss curves
- get accuracy, confusion matrix and classification report on test data


"""

# your code to accomplish the steps above
lr = 5e-6
wd = 5e-2
num_epochs = 30

model = FiveLayerFC(32*32*3,200,200,10,lr,wd).to(device)
model,train_loss,val_loss = train_model(model,trainloader,valloader,num_epochs)

plt.plot(torch.arange(num_epochs),train_loss, label="train_loss")
plt.plot(torch.arange(num_epochs),val_loss, label="val_loss")
plt.legend()
plt.show()

model_eval(model,testloader)

"""# Convolutional network
- complete the class definition below
- The network structure is provided. Feel free to modify it -- in which case, rename the class, and run the experiments below.
- The network structure is a sequence of three Conv2d, ReLU, Conv2D, ReLU, MaxPool2d, BatchNorm2d blocks.
- The final layers include two fully connected layers and an output layer with 10 units.

"""

class ConvModel(nn.Module):
    def __init__(self,lr,wd):
        super().__init__()
        self.lr = lr
        self.wd = wd
        self.net = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # output: 64 x 16 x 16
            nn.BatchNorm2d(64),

            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # output: 128 x 8 x 8
            nn.BatchNorm2d(128),

            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2), # output: 256 x 4 x 4
            nn.BatchNorm2d(256),

            nn.Flatten(),
            nn.Linear(256*4*4, 1024),
            nn.ReLU(),
            nn.Linear(1024, 512),
            nn.ReLU(),
            nn.Linear(512, 10))
        self.configure_optimizers()

    def forward(self,x):
        # forward propagate x through network
        # YOUR CODE HERE
        return model.net(x)

    def loss(self,yhat,y,averaged=True):
        # use nn.functional.cross_entropy() to evaluate loss with prediction (yhat)
        # and truth (y). Average it over a batch.
        # YOUR CODE HERE

        return nn.functional.cross_entropy(yhat, y, reduction='mean')

    def predict(self,X):
        # return the index of the highest output in the output layer
        # YOUR CODE HERE
        return self.net(X).argmax(dim=1, keepdim=True)


    def configure_optimizers(self):
        # set up the Adam optimizer with default parameters and
        # model's learning rate and weight decay
        # YOUR CODE HERE
        self.optimizer = torch.optim.Adam(self.net.parameters(), lr = self.lr, weight_decay = self.wd)

"""# Train the model
- under two sets of hyperparameters
"""

lr = 1e-3
wd = 1e-3
num_epochs = 30

model = ConvModel(lr,wd).to(device)
model,train_loss,val_loss = train_model(model,trainloader,valloader,num_epochs)

# plot the validation and training loss curves
# your code here
plt.plot(torch.arange(num_epochs),train_loss, label="train_loss")
plt.plot(torch.arange(num_epochs),val_loss, label="val_loss")
plt.legend()
plt.show()

model.eval()
test_predictions = []
test_labels = []

with torch.no_grad():
    for data in testloader:
        inputs, labels = data
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs, 1)
        test_predictions.extend(predicted.cpu().numpy())
        test_labels.extend(labels.cpu().numpy())

# Calculate accuracy
accuracy = accuracy_score(test_labels, test_predictions)

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_predictions)

# Classification report
class_report = classification_report(test_labels, test_predictions)

print(f"Accuracy: {accuracy}")
print(f"Confusion Matrix:\n{conf_matrix}")
print(f"Classification Report:\n{class_report}")

# hyperparameter set 2
lr = 1e-4
wd = 1e-4
num_epochs = 20
model = ConvModel(lr,wd).to(device)
model,train_loss,val_loss = train_model(model,trainloader,valloader,num_epochs)

# plot the validation and training loss curves
# your code here


plt.plot(torch.arange(num_epochs),train_loss, label="train_loss")
plt.plot(torch.arange(num_epochs),val_loss, label="val_loss")
plt.legend()
plt.show()

model.eval()
test_predictions = []
test_labels = []

with torch.no_grad():
    for data in testloader:
        inputs, labels = data
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs, 1)
        test_predictions.extend(predicted.cpu().numpy())
        test_labels.extend(labels.cpu().numpy())

# Calculate accuracy
accuracy = accuracy_score(test_labels, test_predictions)

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_predictions)

# Classification report
class_report = classification_report(test_labels, test_predictions)

print(f"Accuracy: {accuracy}")
print(f"Confusion Matrix:\n{conf_matrix}")
print(f"Classification Report:\n{class_report}")

"""Training Five Layer NN to an accuracy of > 50%

"""

lr = 1e-3
wd = 1e-3
num_epochs = 40

model = FiveLayerFC(32*32*3,200,200,10,lr,wd).to(device)
model,train_loss,val_loss = train_model(model,trainloader,valloader,num_epochs)

plt.plot(torch.arange(num_epochs),train_loss, label="train_loss")
plt.plot(torch.arange(num_epochs),val_loss, label="val_loss")
plt.legend()
plt.show()

model.eval()
test_predictions = []
test_labels = []

with torch.no_grad():
    for data in testloader:
        inputs, labels = data
        inputs, labels = inputs.to(device), labels.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs, 1)
        test_predictions.extend(predicted.cpu().numpy())
        test_labels.extend(labels.cpu().numpy())

# Calculate accuracy
accuracy = accuracy_score(test_labels, test_predictions)

# Confusion matrix
conf_matrix = confusion_matrix(test_labels, test_predictions)

# Classification report
class_report = classification_report(test_labels, test_predictions)

print(f"Accuracy: {accuracy}")
print(f"Confusion Matrix:\n{conf_matrix}")
print(f"Classification Report:\n{class_report}")

"""# Comment on
- performance difference between multilayer feedforward and convolutional neural nets
- difference in the number of parameters between the two classes of deep models
- impact of learning rate and weight decay choice on the feedforward networks
- impact of learning rate and weight decay choice on convolutional networks
- experiment with these two hyperparameters to achieve > 50% accuracy with feedforward networks, and > 80% accuracy with convolutional networks


YOUR COMMENTS HERE

*   The fully connected neural network struggled to surpass 50% accuracy and couldn't achieve a loss below 1.0, while the Convnet easily reached over 80% accuracy with a loss of 0.2, resulting in significantly higher F1 scores for each class.
*   The Convnet has around 0.5M fewer parameters than the FF net, primarily attributed to the chosen model architecture. If we were to construct a feed-forward network with an equivalent number of layers as our Convnet, we would notice that the Convnet has substantially fewer parameters due to its sparse connections and weight sharing.
*  The model was training better at the learning rates 1e-3 and wd- 1e-3(gave more than 50 % accuarcy like seen in the last code snippet) . But for 5e-6 and 5e-2 gave around 49% accuracy. we can observe there is a signicficant change observed with changing learning rate and weight decay.
*  In the case of the ConvNet, it became evident that the model performed more effectively with a lower learning rateS compared to 1e-1. While the variation in weight decay during hyperparameter tuning didn't yield a substantial performance difference, a higher weight decay imposed a more pronounced regularization effect on the model, which helped mitigate overfitting.
*   The Feedforward model attained an accuracy exceeding 50% using specific hyperparameters (lr=1e-3 and wd=1e-3) after 40 epochs of training, determined after testing several values. But (lr=5e-6 and wd=5e-2) gave 49% accuracy .Likewise, the Conv model achieved an accuracy greater than 80% with the same hyperparameters (lr=1e-3 and wd=1e-3) but in just 20 epochs of training.(lr=1e-4 and wd=1e-4) in 20 epochs gave 79% like mentioned above
"""