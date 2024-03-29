from concurrent import futures
import nevergrad.optimization as optimization
from nevergrad import instrumentation as instru
import argparse
import subprocess
import shlex
import numpy as np
from time import sleep
import pickle
import glob
import torch
import os
import shutil

def get_file_name(dir_):

	idx = np.random.randint(1)

	fname = dir_ + str(np.random.randint(1,999999999,1)[0]) + '.p'

	while os.path.isfile(fname):
		fname = dir_ + str(np.random.randint(1,999999999,1)[0]) + '.p'

	file_ = open(fname, 'wb')
	pickle.dump(None, file_)
	file_.close()

	return fname

def remove_err_out_files(id_):

	files_list = glob.glob('*'+id_+'*')

	for file_ in files_list:
		os.remove(file_)

# Training settings
parser=argparse.ArgumentParser(description='HP PSO search for ASV')
parser.add_argument('--batch-size', type=int, default=24, metavar='N', help='input batch size for training (default: 24)')
parser.add_argument('--epochs', type=int, default=200, metavar='N', help='number of epochs to train (default: 200)')
parser.add_argument('--budget', type=int, default=30, metavar='N', help='Maximum training runs')
parser.add_argument('--no-cuda', action='store_true', default=False, help='Disables GPU use')
parser.add_argument('--sub-file', type=str, default='./run_hp.sh', metavar='Path', help='Path to sge submission file')
parser.add_argument('--train-hdf-file', type=str, default='./data/train.hdf', metavar='Path', help='Path to hdf data')
parser.add_argument('--valid-hdf-file', type=str, default=None, metavar='Path', help='Path to hdf data')
parser.add_argument('--model', choices=['resnet_stats', 'resnet_mfcc', 'resnet_lstm', 'resnet_small', 'resnet_large', 'all'], default='resnet_lstm', help='Model arch according to input type')
parser.add_argument('--workers', type=int, help='number of data loading workers', default=4)
parser.add_argument('--hp-workers', type=int, help='number of search workers', default=1)
parser.add_argument('--seed', type=int, default=1, metavar='S', help='random seed (default: 1)')
parser.add_argument('--save-every', type=int, default=1, metavar='N', help='how many epochs to wait before logging training status. Default is 1')
parser.add_argument('--ncoef', type=int, default=23, metavar='N', help='number of MFCCs (default: 23)')
parser.add_argument('--n-cycles', type=int, default=3, metavar='N', help='cycles over speakers list to complete 1 epoch')
parser.add_argument('--valid-n-cycles', type=int, default=100, metavar='N', help='cycles over speakers list to complete 1 epoch')
parser.add_argument('--temp-folder', type=str, default='temp', metavar='Path', help='Temp folder for pickle files')
parser.add_argument('--checkpoint-path', type=str, default=None, metavar='Path', help='Path for checkpointing')
args=parser.parse_args()
args.cuda=True if not args.no_cuda else False

def train(lr, l2, momentum, patience, latent_size, n_hidden, hidden_size, n_frames, model, ncoef, dropout_prob, epochs, batch_size, n_workers, cuda, train_hdf_file, valid_hdf_file, n_cycles, valid_n_cycles, submission_file, tmp_dir, cp_path, softmax):

	file_name = get_file_name(tmp_dir)
	np.random.seed()

	command = 'sbatch' + ' ' + submission_file + ' ' + str(lr) + ' ' + str(l2) + ' ' + str(momentum) + ' ' + str(int(patience)) + ' ' + str(int(latent_size)) + ' ' + str(int(n_hidden)) + ' ' + str(int(hidden_size)) + ' ' + str(int(n_frames)) + ' ' + str(model) + ' ' + str(ncoef) + ' ' + str(dropout_prob) + ' ' + str(epochs) + ' ' + str(batch_size) + ' ' + str(n_workers) + ' ' + str(cuda) + ' ' + str(train_hdf_file) + ' ' + str(valid_hdf_file) + ' ' + str(n_cycles) + ' ' + str(valid_n_cycles) + ' ' + str(file_name) + ' ' + str(cp_path) + ' ' + str(file_name.split('/')[-1]+'t')+ ' ' + str(softmax)

	for j in range(10):

		sleep(np.random.randint(10,120,1)[0])

		result=None

		p=subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)

		out = p.communicate()

		job_id = out[0].decode('utf-8').split(' ')[3].strip()

		result_file = open(file_name, 'rb')
		result = pickle.load(result_file)
		result_file.close()

		if result is not None:
			remove_err_out_files(job_id)
			os.remove(file_name)

			print(' ')
			print('Best EER in result file ' + file_name.split('/')[-1].split('.p')[0] + ' was: {}'.format(result))
			print(' ')
			print('With hyperparameters:')
			print('Model: {}'.format(model))
			print('Softmax mode: {}'.format(softmax))
			print('Embeddings size: {}'.format(int(latent_size)))
			print('Number of hidden layers: {}'.format(int(n_hidden)))
			print('Size of hidden layers: {}'.format(int(hidden_size)))
			print('Dropout rate: {}'.format(dropout_prob))
			print('LR: {}'.format(lr))
			print('momentum: {}'.format(momentum))
			print('l2: {}'.format(l2))
			print('Patience: {}'.format(int(patience)))
			print('Max. number of frames: {}'.format(int(n_frames)))
			print(' ')

			return result

	return 0.5

lr=instru.var.Array(1).asfloat().bounded(1, 4).exponentiated(base=10, coeff=-1)
l2=instru.var.Array(1).asfloat().bounded(1, 5).exponentiated(base=10, coeff=-1)
momentum=instru.var.Array(1).asfloat().bounded(0.10, 0.95)
patience=instru.var.Array(1).asfloat().bounded(1, 100)
latent_size=instru.var.Array(1).asfloat().bounded(64, 512)
n_hidden=instru.var.Array(1).asfloat().bounded(1, 6)
hidden_size=instru.var.Array(1).asfloat().bounded(64, 512)
dropout_prob=instru.var.Array(1).asfloat().bounded(0.01, 0.50)
n_frames=instru.var.Array(1).asfloat().bounded(600, 1000)
model=instru.var.OrderedDiscrete(['resnet_mfcc', 'resnet_lstm', 'resnet_stats', 'resnet_small']) if args.model=='all' else args.model
ncoef=args.ncoef
epochs=args.epochs
batch_size=args.batch_size
n_workers=args.workers
cuda=args.cuda
train_hdf_file=args.train_hdf_file
valid_hdf_file=args.valid_hdf_file
n_cycles=args.n_cycles
valid_n_cycles=args.valid_n_cycles
sub_file=args.sub_file
checkpoint_path=args.checkpoint_path
softmax=instru.var.OrderedDiscrete(['softmax', 'am_softmax'])

tmp_dir = os.getcwd() + '/' + args.temp_folder + '/'

if not os.path.isdir(tmp_dir):
	os.mkdir(tmp_dir)

instrum=instru.Instrumentation(lr, l2, momentum, patience, latent_size, n_hidden, hidden_size, n_frames, model, ncoef, dropout_prob, epochs, batch_size, n_workers, cuda, train_hdf_file, valid_hdf_file, n_cycles, valid_n_cycles, sub_file, tmp_dir, checkpoint_path, softmax)

hp_optimizer=optimization.optimizerlib.RandomSearch(instrumentation=instrum, budget=args.budget, num_workers=args.hp_workers)

with futures.ThreadPoolExecutor(max_workers=args.hp_workers) as executor:
	print(hp_optimizer.optimize(train, executor=executor, verbosity=2))

shutil.rmtree(tmp_dir)
