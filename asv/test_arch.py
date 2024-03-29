from __future__ import print_function
import argparse
import torch
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim
import torch.utils.data
import model as model_

# Training settings
parser = argparse.ArgumentParser(description='Test new architectures')
parser.add_argument('--model', choices=['resnet_stats', 'resnet_mfcc', 'resnet_lstm', 'resnet_small', 'resnet_large', 'all'], default='resnet_lstm', help='Model arch according to input type')
parser.add_argument('--ncoef', type=int, default=23, metavar='N', help='number of MFCCs (default: 23)')
parser.add_argument('--latent-size', type=int, default=256, metavar='S', help='latent layer dimension (default: 256)')
parser.add_argument('--hidden-size', type=int, default=512, metavar='S', help='latent layer dimension (default: 512)')
parser.add_argument('--n-hidden', type=int, default=1, metavar='N', help='maximum number of frames per utterance (default: 1)')
args = parser.parse_args()

if args.model == 'resnet_stats' or  args.model == 'all':
	batch = torch.rand(3, 1, args.ncoef, 200)
	model = model_.ResNet_stats(n_z=args.latent_size, nh=args.n_hidden, n_h=args.hidden_size, proj_size=100, ncoef=args.ncoef)
	print('resnet_stats')
	mu = model.forward(batch)
	print(mu.size())
	emb = torch.cat([mu,mu],1)
	print(emb.size())
	pred = model.forward_bin(emb)
	print(pred.size())
	scores_p = model.forward_bin(emb).squeeze()
	print(scores_p.size())
if args.model == 'resnet_mfcc' or  args.model == 'all':
	batch = torch.rand(3, 1, args.ncoef, 200)
	model = model_.ResNet_mfcc(n_z=args.latent_size, nh=args.n_hidden, n_h=args.hidden_size, proj_size=100, ncoef=args.ncoef)
	print('resnet_mfcc')
	mu = model.forward(batch)
	print(mu.size())
	emb = torch.cat([mu,mu],1)
	print(emb.size())
	pred = model.forward_bin(emb)
	print(pred.size())
	scores_p = model.forward_bin(emb).squeeze()
	print(scores_p.size())
if args.model == 'resnet_lstm' or  args.model == 'all':
	batch = torch.rand(3, 1, args.ncoef, 200)
	model = model_.ResNet_lstm(n_z=args.latent_size, nh=args.n_hidden, n_h=args.hidden_size, proj_size=100, ncoef=args.ncoef)
	print('resnet_lstm')
	mu = model.forward(batch)
	print(mu.size())
	emb = torch.cat([mu,mu],1)
	print(emb.size())
	pred = model.forward_bin(emb)
	print(pred.size())
	scores_p = model.forward_bin(emb).squeeze()
	print(scores_p.size())
if args.model == 'resnet_small' or  args.model == 'all':
	batch = torch.rand(3, 1, args.ncoef, 200)
	model = model_.ResNet_small(n_z=args.latent_size, nh=args.n_hidden, n_h=args.hidden_size, proj_size=100, ncoef=args.ncoef)
	print('resnet_small')
	mu = model.forward(batch)
	print(mu.size())
	emb = torch.cat([mu,mu],1)
	print(emb.size())
	pred = model.forward_bin(emb)
	print(pred.size())
	scores_p = model.forward_bin(emb).squeeze()
	print(scores_p.size())
if args.model == 'resnet_large' or  args.model == 'all':
	batch = torch.rand(3, 1, args.ncoef, 200)
	model = model_.ResNet_large(n_z=args.latent_size, nh=args.n_hidden, n_h=args.hidden_size, proj_size=100, ncoef=args.ncoef)
	print('resnet_large')
	mu = model.forward(batch)
	print(mu.size())
	emb = torch.cat([mu,mu],1)
	print(emb.size())
	pred = model.forward_bin(emb)
	print(pred.size())
	scores_p = model.forward_bin(emb).squeeze()
	print(scores_p.size())
