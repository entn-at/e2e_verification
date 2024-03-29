from __future__ import print_function
import argparse
import torch
from torch.utils.data import DataLoader
from train_loop import TrainLoop
import torch.optim as optim
from torchvision import datasets, transforms
from models import vgg, resnet, densenet
import numpy as np
from time import sleep
import os
import sys

def set_np_randomseed(worker_id):
	np.random.seed(np.random.get_state()[1][0]+worker_id)

def get_freer_gpu(trials=10):
	sleep(2)
	for j in range(trials):
		os.system('nvidia-smi -q -d Memory |grep -A4 GPU|grep Free >tmp')
		memory_available = [int(x.split()[2]) for x in open('tmp', 'r').readlines()]
		dev_ = torch.device('cuda:'+str(np.argmax(memory_available)))
		try:
			a = torch.rand(1).cuda(dev_)
			return dev_
		except:
			pass

	print('NO GPU AVAILABLE!!!')
	exit(1)

# Training settings
parser = argparse.ArgumentParser(description='Cifar10 Classification')
parser.add_argument('--batch-size', type=int, default=64, metavar='N', help='input batch size for training (default: 64)')
parser.add_argument('--valid-batch-size', type=int, default=16, metavar='N', help='input batch size for testing (default: 256)')
parser.add_argument('--epochs', type=int, default=500, metavar='N', help='number of epochs to train (default: 500)')
parser.add_argument('--lr', type=float, default=0.1, metavar='LR', help='learning rate (default: 0.1)')
parser.add_argument('--l2', type=float, default=5e-4, metavar='lambda', help='L2 wheight decay coefficient (default: 0.0005)')
parser.add_argument('--patience', type=int, default=10, metavar='S', help='Epochs to wait before decreasing LR by a factor of 0.5 (default: 10)')
parser.add_argument('--momentum', type=float, default=0.9, metavar='lambda', help='Momentum (default: 0.9)')
parser.add_argument('--checkpoint-epoch', type=int, default=None, metavar='N', help='epoch to load for checkpointing. If None, training starts from scratch')
parser.add_argument('--checkpoint-path', type=str, default=None, metavar='Path', help='Path for checkpointing')
parser.add_argument('--data-path', type=str, default='./data/', metavar='Path', help='Path to data')
parser.add_argument('--valid-data-path', type=str, default='./data/', metavar='Path', help='Path to data')
parser.add_argument('--seed', type=int, default=42, metavar='S', help='random seed (default: 42)')
parser.add_argument('--n-workers', type=int, default=4, metavar='N', help='Workers for data loading. Default is 4')
parser.add_argument('--model', choices=['vgg', 'resnet', 'densenet'], default='resnet')
parser.add_argument('--softmax', choices=['softmax', 'am_softmax'], default='softmax', help='Softmax type')
parser.add_argument('--hidden-size', type=int, default=512, metavar='S', help='latent layer dimension (default: 512)')
parser.add_argument('--n-hidden', type=int, default=1, metavar='N', help='maximum number of frames per utterance (default: 1)')
parser.add_argument('--dropout-prob', type=float, default=0.25, metavar='p', help='Dropout probability (default: 0.25)')
parser.add_argument('--save-every', type=int, default=1, metavar='N', help='how many epochs to wait before logging training status. Default is 1')
parser.add_argument('--no-cuda', action='store_true', default=False, help='Disables GPU use')
parser.add_argument('--no-cp', action='store_true', default=False, help='Disables checkpointing')
parser.add_argument('--verbose', type=int, default=1, metavar='N', help='Verbose is activated if > 0')
args = parser.parse_args()
args.cuda = True if not args.no_cuda and torch.cuda.is_available() else False

if args.cuda:
	torch.backends.cudnn.benchmark=True

transform_train = transforms.Compose([transforms.RandomCrop(32, padding=4), transforms.RandomHorizontalFlip(), transforms.ToTensor(),])
transform_test = transforms.ToTensor()

#trainset = Loader(args.data_path)
trainset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform_train)
train_loader = torch.utils.data.DataLoader(trainset, batch_size=args.batch_size, shuffle=True, num_workers=args.n_workers, worker_init_fn=set_np_randomseed)

#validset = Loader(args.valid_data_path)
validset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform_test)
valid_loader = torch.utils.data.DataLoader(validset, batch_size=args.valid_batch_size, shuffle=False, num_workers=args.n_workers)

if args.model == 'vgg':
	model = vgg.VGG('VGG16', nh=args.n_hidden, n_h=args.hidden_size, dropout_prob=args.dropout_prob, sm_type=args.softmax)
elif args.model == 'resnet':
	model = resnet.ResNet18(nh=args.n_hidden, n_h=args.hidden_size, dropout_prob=args.dropout_prob, sm_type=args.softmax)
elif args.model == 'densenet':
	model = densenet.densenet_cifar(nh=args.n_hidden, n_h=args.hidden_size, dropout_prob=args.dropout_prob, sm_type=args.softmax)

if args.cuda:
	device = get_freer_gpu()
	model = model.cuda(device)

optimizer = optim.SGD(model.parameters(), lr=args.lr, weight_decay=args.l2, momentum=args.momentum)

trainer = TrainLoop(model, optimizer, train_loader, valid_loader, patience=args.patience, verbose=args.verbose, save_cp=(not args.no_cp), checkpoint_path=args.checkpoint_path, checkpoint_epoch=args.checkpoint_epoch, cuda=args.cuda)

if args.verbose >0:
	print('Cuda Mode is: {}'.format(args.cuda))
	print('Selected model: {}'.format(args.model))
	print('Batch size: {}'.format(args.batch_size))
	print('LR: {}'.format(args.lr))
	print('Momentum: {}'.format(args.momentum))
	print('l2: {}'.format(args.l2))
	print('Patience: {}'.format(args.patience))
	print('Dropout rate: {}'.format(args.dropout_prob))
	print('Softmax Mode is: {}'.format(args.softmax))

trainer.train(n_epochs=args.epochs, save_every=args.save_every)
