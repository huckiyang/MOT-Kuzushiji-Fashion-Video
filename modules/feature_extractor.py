import numpy as np
import torch
import torch.nn as nn
import modules.submodules as smd
import modules.utils as utils

#FeatureExtractor的结构
#就是普通的全卷积网络

# super(Conv, self).__init__()
# self.layer_num = len(conv_features) - 1
# self.out_sizes = out_sizes
# assert self.layer_num == len(conv_kernels) == len(out_sizes) > 0, 'Invalid conv parameters'
# self.bn = bn
# self.dp = dp
# # Convolutional block
# for i in range(0, self.layer_num):
#     setattr(self, 'conv'+str(i), nn.Conv2d(conv_features[i], conv_features[i+1],
#         (conv_kernels[i][0], conv_kernels[i][1]), stride=1,
#         padding=(conv_kernels[i][0]//2, conv_kernels[i][1]//2)))
#     if bn == 1:
#         setattr(self, 'bn'+str(i), nn.BatchNorm2d(conv_features[i+1]))
#     setattr(self, 'pool'+str(i), nn.AdaptiveMaxPool2d(tuple(out_sizes[i])))
#     if dp == 1:
#         setattr(self, 'dp'+str(i), nn.Dropout2d(0.2))
# # Transformations
# self.tranform = func('relu')


class FeatureExtractor(nn.Module):

    def __init__(self, o):
        super(FeatureExtractor, self).__init__()
        self.o = o
        params = o.cnn.copy()
        params['conv_features'] = [o.D+2] + params['conv_features']
        self.cnn = smd.Conv(params['conv_features'], params['conv_kernels'], params['out_sizes'], bn=params['bn'])

    def forward(self, X_seq):
        o = self.o
        X_seq = X_seq.view(-1, X_seq.size(2), X_seq.size(3), X_seq.size(4))  # NT * D+2 * H * W        
        C3_seq = self.cnn(X_seq)                                             # NT * C3_3 * C3_1 * C3_2
        C3_seq = C3_seq.permute(0, 2, 3, 1)                                  # NT * C3_1 * C3_2 * C3_3
        C2_seq = C3_seq.reshape(-1, o.T, o.dim_C2_1, o.dim_C2_2)             # N * T * C2_1 * C2_2
        return C2_seq