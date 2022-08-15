# -*- coding: utf-8 -*-
"""Copy of Retinal disease.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NyG1vbX3oGXcenbpbv_QGZZ6KR5a2JXx
"""

from google.colab import drive
drive.mount('/content/drive')

import cv2, os
import numpy as np
import pandas as pd

# # !unzip "/content/drive/MyDrive/rohit/resized.zip" -d "/content"
# !unzip "/content/drive/MyDrive/research/rohit/resized.zip" -d "/content"

!unzip "/content/drive/MyDrive/research/rohit/processed.zip" -d "/content"

!pip install tqdm

!zip -r drive/MyDrive/research/rohit/512resized.zip content/resized

folder_dir = "content/processed"
dest_dir = "content/resized"

# img_size = 224
img_size = 512

from tqdm.notebook import tqdm

for images in tqdm(os.listdir(folder_dir)):
  img = cv2.imread(os.path.join(folder_dir,images))
  gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
  _,thresh = cv2.threshold(gray,0,255,cv2.THRESH_OTSU)
  # contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
  # cnt = contours[0]
  x,y,w,h = cv2.boundingRect(thresh)
  crop = img[y:y+h,x:x+w]
  crop = cv2.resize(crop,(img_size,img_size))
  cv2.imwrite(os.path.join(dest_dir,images),crop)

import cv2, os
import numpy as np
import pandas as pd

df_full = pd.read_excel("/content/drive/MyDrive/research/rohit/data.xlsx")
df_full['Patient Sex'] = df_full['Patient Sex'].apply(lambda x: 0 if x=='Female' else 1)

df_full

columns = ['N', 'D', 'G', 'C', 'A', 'H', 'M', 'O']

zero_cols = {c: 0 for c in columns}

def correct_class(row, col_name):
  
  if(row['N']!=1 and "normal fundus" in str(row[col_name]).lower()):
    # print("======before====")
    # print(row)
    row[columns] = 0
    row['N'] = 1
    # print("======after====")
    # print(row)

  a = "".join(str(x) for x in row[columns].tolist())
  row['target'] = a
  return row

  # return row

df_left = df_full.drop(['Right-Fundus', 'Right-Diagnostic Keywords'], axis=1).copy()
df_right = df_full.drop(['Left-Fundus', 'Left-Diagnostic Keywords'], axis=1).copy()

df_left = df_left.apply(lambda x: correct_class(x, 'Left-Diagnostic Keywords'), axis=1)
df_right = df_right.apply(lambda x: correct_class(x, 'Right-Diagnostic Keywords'), axis=1)

df_left.drop(columns, axis=1, inplace=True)
df_right.drop(columns, axis=1, inplace=True)

# TODO: one hot encode diagnostic keywords late

df_left.rename(columns={'Left-Fundus': 'Fundus', 'Left-Diagnostic Keywords': 'Diagnostic Keywords'}, inplace=True)
df_right.rename(columns={'Right-Fundus': 'Fundus', 'Right-Diagnostic Keywords': 'Diagnostic Keywords'}, inplace=True)
df = df_left.append(df_right)

df

import os, shutil
root_dir='content/resized/'

main_dir = 'dataset'
def copy_to_folders(row):
  os.makedirs(os.path.join(main_dir, row['target']), exist_ok=True) 
  shutil.copy(os.path.join(root_dir, row['Fundus']), os.path.join(main_dir, row['target']))

df.apply(lambda x: copy_to_folders(x), axis=1)

from sklearn.preprocessing import LabelEncoder

labelencoder = LabelEncoder()

df.target = labelencoder.fit_transform(df.target)

df

len(labelencoder.classes_)

# !zip -r dataset.zip dataset

# df.to_csv('dataset.csv')
from sklearn.model_selection import train_test_split

train, val = train_test_split(df, test_size=0.2)
train.to_csv('train.csv')
val.to_csv('val.csv')

# df[columns].iloc[0]

import torch
# import torch.cuda as cuda
import torch.nn as nn

from torch.autograd import Variable

from torchvision import datasets
from torchvision import transforms

# The functional module contains helper functions for defining neural network layers as simple functions
import torch.nn.functional as F

import matplotlib.pyplot as plt

import numpy as np

import torchvision.models as models

from torch.optim import lr_scheduler

import torch.optim as optim

import os

from torch.utils.data import Dataset
from PIL import Image
import torchvision

class RetinalDataset(Dataset):

    def __init__(self, csv_file, root_dir, transform=None, x_col='Fundus', y_cols=columns):

        self.retinal_data = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform
        self.x_col = x_col
        self.y_cols = y_cols
        self.classes = y_cols

    def __len__(self):
        return len(self.retinal_data)

    def __getitem__(self, idx):
        img_name = os.path.join(self.root_dir,
                                self.retinal_data[self.x_col].iloc[idx])
        image = Image.open(img_name).convert("RGB")

        if self.transform:
          image = self.transform(image)

        y_label = self.retinal_data[self.y_cols].iloc[idx]
        # y_label = np.array([y_label])
        # y_label = y_label.astype('float32').reshape(-1)

        return (image, y_label)

from torchvision import datasets
from torchvision import transforms
from torch.utils.data.sampler import SubsetRandomSampler

data_transforms = {
    'train': transforms.Compose([
        transforms.ToTensor(),                         
        transforms.RandomHorizontalFlip(),
    ]),
    'val': transforms.Compose([
        transforms.ToTensor(),
    ]),
}

data_dir = 'dataset'

full_dataset = datasets.ImageFolder(data_dir, data_transforms['train'])

batch_size = 1
validation_split = .2
shuffle_dataset = True
random_seed= 42

# Creating data indices for training and validation splits:
dataset_size = len(full_dataset)
indices = list(range(dataset_size))
split = int(np.floor(validation_split * dataset_size))
if shuffle_dataset :
    np.random.seed(random_seed)
    np.random.shuffle(indices)
train_indices, val_indices = indices[split:], indices[:split]

# Creating PT data samplers and loaders:
train_sampler = SubsetRandomSampler(train_indices)
valid_sampler = SubsetRandomSampler(val_indices)

samplers = {'train': train_sampler, 'val': valid_sampler}

# train_loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, 
#                                            sampler=train_sampler)
# validation_loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
#                                                 sampler=valid_sampler)

dataloaders = {x: torch.utils.data.DataLoader(full_dataset, batch_size=16, sampler=samplers[x],
                                             num_workers=0, pin_memory=True)
              for x in ['train', 'val']}

dataset_sizes = {x: len(samplers[x]) for x in ['train', 'val']}
class_names = labelencoder.classes_

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# # Data augmentation and normalization for training
# # Just normalization for validation
# data_transforms = {
#     'train': transforms.Compose([
#         transforms.ToTensor(),                         
#         transforms.RandomHorizontalFlip(),
#     ]),
#     'val': transforms.Compose([
#         transforms.ToTensor(),
#     ]),
# }

# data_dir = 'data'
# image_datasets = {x: RetinalDataset(csv_file=f'{x}.csv', root_dir='content/resized/', transform=data_transforms[x], y_cols='target')
#                   for x in ['train', 'val']}
# # _dataset = RetinalDataset(csv_file='dataset.csv', root_dir='content/resized/', transform=data_transforms['train'])

# dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=16,
#                                              shuffle=True, num_workers=0, pin_memory=True)
#               for x in ['train', 'val']}
# dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
# class_names = labelencoder.classes_

# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# device='cpu'

"""## Model"""

# import torch.nn as nn
# import torchvision.models as models

# class VGG19(nn.Module):
#     def __init__(self, train_CNN=False, num_classes=1):
#         super(VGG19, self).__init__()
#         self.train_CNN = train_CNN
#         self.vgg = models.vgg19(pretrained=True)
#         for param in self.vgg.parameters():
#             param.requires_grad = False
#         self.linear = nn.Linear(self.vgg.classifier[-1].out_features, 512)
#         self.out = nn.Linear(512, num_classes)
        
#         self.relu = nn.ReLU()
#         # self.dropout = nn.Dropout(0.5)
#         self.sigmoid = nn.Sigmoid()

#     def forward(self, images):
#         x = self.vgg(images)
#         x = self.linear(x)
#         x = self.relu(x)
#         x = self.out(x)
#         x = self.relu(x)
#         return x

# model_res = models.resnet152(pretrained=True, progress=True)

# for param in model_res.parameters():
#     param.requires_grad = True

# num_ftrs = model_res.fc.in_features
# model_res.fc = nn.Sequential(
#                         nn.Linear(num_ftrs, 400),
#                         nn.Linear(400, len(labelencoder.classes_)),
#                         nn.Softmax(-1)
#                     )

# model = model_res.to(device)

model_res = models.mobilenet_v3_large(pretrained=True, progress=True)

for param in model_res.parameters():
    param.requires_grad = True

num_ftrs = model_res.classifier[-1].in_features
model_res.classifier[-1] = nn.Linear(num_ftrs, len(labelencoder.classes_))

model = model_res.to(device)


criterion = nn.CrossEntropyLoss()
# Observe that all parameters are being optimized
optimizer_ft = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
# optimizer_ft = optim.Adam(model.parameters(), lr=0.0001)

# Decay LR by a factor of 0.1 every 7 epochs
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)

# # model = VGG19(num_classes=len(columns)).to(device)
# model_vgg = models.vgg19(pretrained=True, progress=True)
# for param in model_vgg.parameters():
#     param.requires_grad = False

# num_ftrs = model_vgg.classifier[6].in_features
# model_vgg.classifier[6] = nn.Sequential(
#                         nn.Linear(num_ftrs, 400),
#                         nn.Linear(400, 8),
#                         nn.Sigmoid()
#                     )

# model = model_vgg.to(device)


# criterion = nn.MSELoss()
# # Observe that all parameters are being optimized
# # optimizer_ft = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
# optimizer_ft = optim.Adam(model.parameters(), lr=0.0001)

# # Decay LR by a factor of 0.1 every 7 epochs
# exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)

import copy, time

def train_model(model, criterion, optimizer, scheduler, num_epochs=25):
    since = time.time()
    train_loss = []
    test_loss = []
    train_accuracy = []
    test_accuracy = []

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # Each epoch has a training and validation phase
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()  # Set model to training mode
            else:
                model.eval()   # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data.
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward
                # track history if only in train
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    # backward + optimize only if in training phase
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                # statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            if phase == 'train':
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]
            
            if phase == 'train':
                train_loss.append(epoch_loss)
                train_accuracy.append(epoch_acc)
            else:
                test_loss.append(epoch_loss)
                test_accuracy.append(epoch_acc)

            print('{} Loss: {:.4f} Acc: {:.4f}'.format(
                phase, epoch_loss, epoch_acc))

            # deep copy the model
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

        print()

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))

    # load best model weights
    model.load_state_dict(best_model_wts)
    return model, train_loss, train_accuracy, test_loss, test_accuracy

model, train_loss, train_accuracy, test_loss, test_accuracy = train_model(model, criterion, optimizer_ft, exp_lr_scheduler,
                       num_epochs=25)

test_image = next(iter(dataloaders['val']))

out = model(test_image[0].to(device))

out.shape

test_image[1]

criterion(out, test_image[1].to(device))

a = test_image[1].reshape(-1).long()

out.dtype

a

