import os
import os.path as path
import argparse
import subprocess
from joblib import Parallel, delayed
import multiprocessing
import math
# import cv2
import numpy as np
import torch
import sys
sys.path.append("modules")
import utils
import torchvision
# Importing Image module from PIL package  
from PIL import Image  
import PIL  
import time as ti
from scipy import ndimage
# from imageshuffle import imageshuffle
# from imageshuffle import imagescramble
import random
from torchvision import transforms as transforms

parser = argparse.ArgumentParser()
parser.add_argument('--v', type=int, default=0)
parser.add_argument('--metric', type=int, default=0)
parser.add_argument('--noise', type=int, default=0, choices=[0, 1, 2, 3, 4],
                    help="Choose for a clean (0), noisy (1), or filter (2) model")
parser.add_argument('--mnist', type=str, default='MNIST', choices=['MNIST', 'FashionMNIST', 'KMNIST'], help="Choose for MNIST, Fashion, or Kuzushiji")
parser.add_argument('--noise_lv', type=float, default=0.3)
parser.add_argument('--optim', type=str, default='adam', choices=['adam', 'adabound'], help="Choose for optimizer")

arg = parser.parse_args()

N = 1 if arg.metric == 1 else 16#32#64
T = 20
H = 128
W = 128
D = 1
h = 28
w = 28
O = 3
# frame_num = 1e4 if arg.metric == 1 else 2e6
frame_num = 1e3 if arg.metric == 1 else 2e6
train_ratio = 0 if arg.metric == 1 else 0.96
birth_prob = 0.5
appear_interval = 5
scale_var = 0
ratio_var = 0
velocity = 5.3
task = 'mnist'
m = h // 3
eps = 1e-5

txt_name = 'gt.txt'
metric_dir = 'metric/' if arg.metric == 1 else ''
data_dir = path.join('data', task)
input_dir = path.join(data_dir, arg.mnist, 'processed')
output_dir = path.join(data_dir, arg.mnist, 'pt', metric_dir)
output_input_dir = path.join(output_dir, 'input')
output_gt_dir = path.join(output_dir, 'gt')
if arg.v == 0:
    utils.rmdir(output_input_dir); utils.mkdir(output_input_dir)
    utils.rmdir(output_gt_dir); utils.mkdir(output_gt_dir)


# mnist data
if not path.exists(input_dir):
    import torchvision.datasets as datasets
    if arg.mnist =='MNIST':
        datasets.MNIST(root=data_dir, train=True, download=True)
    elif arg.mnist =='KMNIST':
        datasets.KMNIST(root=data_dir, train=True, download=True)
    elif arg.mnist =='FashionMNIST':
        datasets.FashionMNIST(root=data_dir, train=True, download=True)

train_data = torch.load(path.join(input_dir, 'training.pt')) # 60000 * 28 * 28
test_data = torch.load(path.join(input_dir, 'test.pt')) # 10000 * 28 * 28

data = torch.cat((train_data[0], test_data[0]), 0).unsqueeze(3) # 70000 * h * w * D
data_num = data.size(0)

# generate data from trackers
train_frame_num = frame_num * train_ratio
test_frame_num = frame_num * (1 - train_ratio)
print('train frame number: ' + str(train_frame_num))
print('test frame number: ' + str(test_frame_num))
batch_nums = {
    'train': math.floor(train_frame_num / (N * T)),
    'test': math.floor(test_frame_num / (N * T))
}


# core_num = 1 if arg.metric == 1 else multiprocessing.cpu_count()
core_num = multiprocessing.cpu_count()
oid = 0 # object id
print("Running with " + str(core_num) + " cores.")
if arg.metric == 1:
    utils.mkdir(output_gt_dir)
    file = open(path.join(output_gt_dir, txt_name), "w")
def process_batch(states, batch_id):
    global oid
    buffer_big = torch.ByteTensor(2, H + 2 * h, W + 2 * w, D).zero_()
    org_seq = torch.ByteTensor(T, H, W, D).zero_()
    # sample all the random variables
    unif = torch.rand(T, O)
    data_id = torch.rand(T, O).mul_(data_num).floor_().long()
    direction_id = torch.rand(T, O).mul_(4).floor_().long() # [0, 3]
    position_id = torch.rand(T, O, 2).mul_(H-2*m).add_(m).floor_().long() # [m, H-m-1]
    scales = torch.rand(T, O).mul_(2).add_(-1).mul_(scale_var).add_(1) # [1 - var, 1 + var]
    ratios = torch.rand(T, O).mul_(2).add_(-1).mul_(ratio_var).add_(1).sqrt_() # [sqrt(1 - var), sqrt(1 + var)]
    for t in range(0, T):
        for o in range(0, O):
            if states[o][0] < appear_interval: # wait for interval frames 
                states[o][0] = states[o][0] + 1
            elif states[o][0] == appear_interval: # allow birth
                if unif[t][o].item() < birth_prob: # birth
                    # shape and appearance
                    data_ind = data_id[t][o].item()
                    scale = scales[t][o].item()
                    ratio = ratios[t][o].item()
                    h_, w_ = round(h * scale * ratio), round(w * scale / ratio)
                    data_patch = data[data_ind]
                    # data_patch = utils.imresize(data[data_ind], h_, w_).unsqueeze(2)
                    # pose
                    direction = direction_id[t][o].item()
                    position = position_id[t][o]
                    x1, y1, x2, y2 = None, None, None, None
                    if direction == 0:
                        x1 = position[0].item()
                        y1 = m
                        x2 = position[1].item()
                        y2 = H - 1 - m
                    elif direction == 1:
                        x1 = position[0].item()
                        y1 = H - 1 - m
                        x2 = position[1].item()
                        y2 = m
                    elif direction == 2:
                        x1 = m
                        y1 = position[0].item()
                        x2 = W - 1 - m
                        y2 = position[1].item()
                    else:
                        x1 = W - 1 - m
                        y1 = position[0].item()
                        x2 = m
                        y2 = position[1].item()
                    theta = math.atan2(y2 - y1, x2 - x1)
                    vx = velocity * math.cos(theta)
                    vy = velocity * math.sin(theta)
                    # initial states
                    states[o] = [appear_interval + 1, data_patch, [], x1, y1, vx, vy, 0, oid]
                    oid += 1
            else:  # exists
                data_patch = states[o][1]
                x1, y1, vx, vy = states[o][3], states[o][4], states[o][5], states[o][6]
                step = states[o][7]
                x = round(x1 + step * vx)
                y = round(y1 + step * vy)
                if x < m-eps or x > W-1-m+eps or y < m-eps or y > H-1-m+eps: # the object disappears
                    states[o][0] = 0
                else:
                    h_, w_ = data_patch.size(0), data_patch.size(1)
                    # center and start position for the big image
                    center_x = x + w
                    center_y = y + h
                    top = math.floor(center_y - (h_ - 1) / 2)
                    left = math.floor(center_x - (w_ - 1) / 2)
                    # put the patch on image
                    img = buffer_big[0].zero_()

                    # if arg.noise == 1: ## with noise [128, 128, 1]
                    #     data_patch = data_patch + (arg.noise_lv*torch.randn(128, 28, dtype=torch.double).view(128,128,1))
                    # elif arg.noise == 2:
                    #     # kernel = np.ones((4,4), np.uint8)
                    #     data_patch = torch.from_numpy(ndimage.binary_dilation(data_patch.numpy(), iterations = 10).astype(data_patch.numpy().dtype)).float()
                    # elif arg.noise == 3:
                    #     # print(data_patch.size())
                    #     # key = 1234
                    #     # enc_s = imageshuffle.Rand(key)
                    #     # data_patch = torch.from_numpy(enc_s.enc(data_patch.numpy())).float()
                    #     # ksize = data_patch.size()
                    #     # data_patch=np.uint8(data_patch)
                    #     # trs=transforms.Compose([transforms.ToPILImage(), transforms.RandomRotation(1, resample=False, expand=False, center=None), transforms.Resize(28), transforms.ToTensor()])
                    #     # data_patch = trs(data_patch).view(ksize)
                    #     # print(data_patch.size())
                    #     # data_patch = data_patch.permute(1,2,0)

                    #     data_patch =  torch.flip(data_patch, [1, 0])

                        # idx = torch.randperm(data_patch.nelement())
                        # data_patch = data_patch.view(-1)[idx].view(data_patch.size())

                    img.narrow(0, top, h_).narrow(1, left, w_).copy_(data_patch)
                    img = img.narrow(0, h, H).narrow(1, w, W) # H * W * D
                    # synthesize a new frame
                    img_f = img.float()
                    org_img_f = org_seq[t].float() # H * W * D
                    if arg.noise == 4: ## with noise [128, 128, 1]
                        org_img_f = org_img_f + (arg.noise_lv*torch.randn(128, 128, dtype=torch.float).view(128,128,1))

                    syn_image = (org_img_f + img_f).clamp_(max=255)
                    # print("ori",syn_image)
                    # print("\n max - min",torch.max(syn_image),torch.min(syn_image))
                    # exit()
                    
                    if arg.noise != 0:
                        show_img1 = torchvision.transforms.ToPILImage()(np.uint8(syn_image.round()))
                        show_img1.save("img_show/" + arg.mnist +'/'+ 'scram'+str(arg.noise) +'_'+str(o)+'_'+ str(t)  + ".png","PNG")
                        # syn_image = syn_image + 0.1*torch.mean(syn_image)
                    # exit()
                    org_seq[t].copy_(syn_image.round().byte())
                    # update the position
                    states[o][7] = states[o][7] + 1
                    # save for metric evaluation
                    if arg.metric == 1:
                        file.write("%d,%d,%.3f,%.3f,%.3f,%.3f,1,-1,-1,-1\n" % 
                            (batch_id*T+t+1, states[o][8]+1, left-w+1, top-h+1, w_, h_))
    return org_seq, states


states_batch = []
for n in range(0, N):
    states_batch.append([])
    for o in range(0, O):
        states_batch[n].append([0]) # the states of the o-th object in the n-th sample
with Parallel(n_jobs=core_num, backend="threading") as parallel:
    for split in ['train', 'test']:
        S = batch_nums[split]
        for s in range(0, S): # for each batch of sequences
            out_batch = parallel(delayed(process_batch)(states_batch[n], s) for n in range(0, N)) # N * 2 * T * H * W * D
            out_batch = list(zip(*out_batch)) # 2 * N * T * H * W * D
            org_seq_batch = torch.stack(out_batch[0], dim=0) # N * T * H * W * D
            states_batch = out_batch[1] # N * []
            if arg.v == 1:
                for t in range(0, T):
                    utils.imshow(org_seq_batch[0, t], 400, 400, 'img', 50)
            else:
                org_seq_batch = org_seq_batch.permute(0, 1, 4, 2, 3) # N * T * D * H * W
                filename = split + '_' + str(s) + '.pt'
                torch.save(org_seq_batch, path.join(output_input_dir, filename))
            print(split + ': ' + str(s+1) + ' / ' + str(S))
if arg.metric == 1:
    file.close()

# save the data configuration
data_config = {
    'task': task,
    'train_batch_num': batch_nums['train'], 
    'test_batch_num': batch_nums['test'],
    'N': N,
    'T': T,
    'D': D,
    'H': H,
    'W': W,
    'h': h,
    'w': w,
    'zeta_s': scale_var,
    'zeta_r': [1, ratio_var]
}
utils.save_json(data_config, path.join(output_dir, 'data_config.json'))
