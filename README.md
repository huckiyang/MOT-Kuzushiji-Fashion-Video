# MOT-Kuzushiji-Fashion-Video
Kuzushiji and Fashion Dataset provided in Robust Unsupervised Multi-Object Tracking in Noisy Environments 2021

## Generate Dataset

- Generate Kuzushiji Video without noise

```
python gen_mot_data.py --mnist KMNIST --noise_lv 0

```

![img](https://github.com/huckiyang/MOT-Kuzushiji-Fashion-Video/blob/main/img_demo/kmnist.gif)


- Generate Fashion Video without noise

```
python gen_mot_data.py --mnist FashionMNIST --noise_lv 0

```

![img](https://github.com/huckiyang/MOT-Kuzushiji-Fashion-Video/blob/main/img_demo/fashion.gif)


- Generate Scrambling Video for testing

Use the [line 193](https://github.com/huckiyang/MOT-Kuzushiji-Fashion-Video/blob/main/gen_mot_data.py#L193) with MNIST data.

![img](https://github.com/huckiyang/MOT-Kuzushiji-Fashion-Video/blob/main/img_demo/scrambling2.gif)



## References

The code is heavily borrowed from [Zhen He et al. tracking by animation](https://github.com/zhen-he/tracking-by-animation). Thanks the authors for their contributions. 

- [FashionMNIST Paper](https://arxiv.org/pdf/1708.07747.pdf)

- [KMNIST Paper](https://arxiv.org/pdf/1812.01718v1.pdf)

[Paper](https://arxiv.org/pdf/2105.10005.pdf) | [Poster](https://github.com/huckiyang/MOT-Kuzushiji-Fashion-Video/blob/main/Huck_ICIP21_Poster.pdf) | [Slides](https://docs.google.com/presentation/d/1GFItGucAZOFi3VBtwbNM9S1M0jLcgpss1ph-r6y8l9U/edit?usp=sharing)

```bib
@INPROCEEDINGS{9506029,  
author={Huck Yang, C.-H. and Chhabra, Mohit and Liu, Y.-C. and Kong, Quan and Yoshinaga, Tomoaki and Murakami, Tomokazu},  
booktitle={2021 IEEE International Conference on Image Processing (ICIP)},   
title={Robust Unsupervised Multi-Object Tracking In Noisy Environments},   
year={2021},  volume={},  number={},  pages={2239-2243},  doi={10.1109/ICIP42928.2021.9506029}}
```
