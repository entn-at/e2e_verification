from concurrent import futures
import nevergrad.optimization as optimization
from nevergrad import instrumentation as instru
import argparse
import torch
from train_loop import TrainLoop
import torch.optim as optim
import torch.utils.data
import model as model_
import numpy as np
from data_load import Loader, Loader_softmax, Loader_mining, Loader_pretrain, Loader_test
import os
import sys

from utils.utils import *

def get_file_name(dir_):

	idx = np.random.randint(1)

	fname = dir_ + '/' + str(np.random.randint(1,999999999,1)[0]) + '.pt'

	while os.path.isfile(fname):
		fname = dir_ + '/' + str(np.random.randint(1,999999999,1)[0]) + '.pt'

	file_ = open(fname, 'wb')
	pickle.dump(None, file_)
	file_.close()

	return fname

# Training settings
parser=argparse.ArgumentParser(description='HP random search for ASV')
parser.add_argument('--batch-size', type=int, default=24, metavar='N', help='input batch size for training (default: 24)')
parser.add_argument('--epochs', type=int, default=200, metavar='N', help='number of epochs to train (default: 200)')
parser.add_argument('--budget', type=int, default=30, metavar='N', help='Maximum training runs')
parser.add_argument('--no-cuda', action='store_true', default=False, help='Disables GPU use')
parser.add_argument('--model', choices=['resnet_stats', 'resnet_mfcc', 'resnet_lstm', 'resnet_small', 'resnet_large', 'all'], default='resnet_lstm', help='Model arch according to input type')
parser.add_argument('--softmax', choices=['softmax', 'am_softmax'], default='softmax', help='Softmax type')
parser.add_argument('--workers', type=int, help='number of data loading workers', default=4)
parser.add_argument('--hp-workers', type=int, help='number of search workers', default=1)
parser.add_argument('--seed', type=int, default=1, metavar='S', help='random seed (default: 1)')
parser.add_argument('--save-every', type=int, default=1, metavar='N', help='how many epochs to wait before logging training status. Default is 1')
parser.add_argument('--ncoef', type=int, default=23, metavar='N', help='number of MFCCs (default: 23)')
parser.add_argument('--valid-n-cycles', type=int, default=500, metavar='N', help='cycles over speakers list to complete 1 epoch')
parser.add_argument('--checkpoint-path', type=str, default=None, metavar='Path', help='Path for checkpointing')
args=parser.parse_args()
args.cuda=True if not args.no_cuda and torch.cuda.is_available() else False

def train(lr, l2, momentum, patience, latent_size, n_hidden, hidden_size, n_frames, model, ncoef, dropout_prob, epochs, batch_size, n_workers, cuda, train_hdf_file, valid_hdf_file, valid_n_cycles, cp_path, softmax):

	if cuda:
		device=get_freer_gpu()

	train_dataset=Loader_test(hdf5_name=train_hdf_file, max_nb_frames=int(n_frames))
	train_loader=torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=False, num_workers=n_workers, worker_init_fn=set_np_randomseed)

	valid_dataset = Loader(hdf5_name = valid_hdf_file, max_nb_frames = int(n_frames), n_cycles=valid_n_cycles)
	valid_loader=torch.utils.data.DataLoader(valid_dataset, batch_size=batch_size, shuffle=False, num_workers=n_workers, worker_init_fn=set_np_randomseed)

	if args.model == 'resnet_stats':
		model = model_.ResNet_stats(n_z=int(latent_size), nh=int(n_hidden), n_h=int(hidden_size), proj_size=len(train_dataset.speakers_list), ncoef=ncoef, dropout_prob=dropout_prob, sm_type=softmax)
	elif args.model == 'resnet_mfcc':
		model = model_.ResNet_mfcc(n_z=int(latent_size), nh=int(n_hidden), n_h=int(hidden_size), proj_size=len(train_dataset.speakers_list), ncoef=ncoef, dropout_prob=dropout_prob, sm_type=softmax)
	if args.model == 'resnet_lstm':
		model = model_.ResNet_lstm(n_z=int(latent_size), nh=int(n_hidden), n_h=int(hidden_size), proj_size=len(train_dataset.speakers_list), ncoef=ncoef, dropout_prob=dropout_prob, sm_type=softmax)
	elif args.model == 'resnet_small':
		model = model_.ResNet_small(n_z=int(latent_size), nh=int(n_hidden), n_h=int(hidden_size), proj_size=len(train_dataset.speakers_list), ncoef=ncoef, dropout_prob=dropout_prob, sm_type=softmax)
	elif args.model == 'resnet_large':
		model = model_.ResNet_large(n_z=int(latent_size), nh=int(n_hidden), n_h=int(hidden_size), proj_size=len(train_dataset.speakers_list), ncoef=ncoef, dropout_prob=dropout_prob, sm_type=softmax)

	if cuda:
		model=model.cuda(device)
	else:
		device=None

	optimizer=optim.SGD(model.parameters(), lr=lr, momentum=momentum, weight_decay=l2)

	trainer=TrainLoop(model, optimizer, train_loader, valid_loader, patience=int(patience), verbose=-1, device=device, cp_name=get_file_name(cp_path), save_cp=False, checkpoint_path=cp_path, pretrain=False, cuda=cuda)

	return trainer.train(n_epochs=epochs)

lr=instru.var.Array(1).asfloat().bounded(1, 4).exponentiated(base=10, coeff=-1)
l2=instru.var.Array(1).asfloat().bounded(1, 5).exponentiated(base=10, coeff=-1)
momentum=instru.var.Array(1).asfloat().bounded(0.10, 0.95)
patience=instru.var.Array(1).asfloat().bounded(1, 100)
latent_size=instru.var.Array(1).asfloat().bounded(64, 512)
n_hidden=instru.var.Array(1).asfloat().bounded(1, 6)
hidden_size=instru.var.Array(1).asfloat().bounded(64, 512)
n_frames=instru.var.Array(1).asfloat().bounded(600, 1000)
dropout_prob=instru.var.Array(1).asfloat().bounded(0.01, 0.50)
model=instru.var.OrderedDiscrete(['resnet_mfcc', 'resnet_lstm', 'resnet_stats', 'resnet_small']) if args.model=='all' else args.model
ncoef=args.ncoef
epochs=args.epochs
batch_size=args.batch_size
n_workers=args.workers
cuda=args.cuda
train_hdf_file=args.train_hdf_file
data_info_path=args.data_info_path
valid_hdf_file=args.valid_hdf_file
valid_n_cycles=args.valid_n_cycles
checkpoint_path=args.checkpoint_path
softmax=instru.var.OrderedDiscrete(['softmax', 'am_softmax'])

instrum=instru.Instrumentation(lr, l2, momentum, patience, latent_size, n_hidden, hidden_size, n_frames, model, ncoef, dropout_prob, epochs, batch_size, n_workers, cuda, train_hdf_file, data_info_path, valid_hdf_file, valid_n_cycles, checkpoint_path, softmax)

hp_optimizer=optimization.optimizerlib.RandomSearch(instrumentation=instrum, budget=args.budget, num_workers=args.hp_workers)

with futures.ThreadPoolExecutor(max_workers=args.hp_workers) as executor:
	print(hp_optimizer.optimize(train, executor=executor))
