#!/usr/bin/env python3
# -*-coding:utf8 -*-
# @TIME     :2019/3/25 下午4:33
# @Author   :hwwu
# @File     :predict.py


import numpy as np
import sys, os
import time
import tensorflow as tf

sys.path.append(os.getcwd())

# crnn packages
import torch
from torch.autograd import Variable
import utils
import dataset
from PIL import Image, ImageFilter
import models.crnn as crnn
import alphabets

str1 = alphabets.alphabet

import argparse

tf.app.flags.DEFINE_string('test_data_path', '/content/test_cptn_result', '')
tf.app.flags.DEFINE_string('output_path', './', '')
FLAGS = tf.app.flags.FLAGS


def get_images():
    files = []
    exts = ['jpg', 'png', 'jpeg', 'JPG']
    for parent, dirnames, filenames in os.walk(FLAGS.test_data_path):
        for filename in filenames:
            for ext in exts:
                if filename.endswith(ext):
                    files.append(os.path.join(parent, filename))
                    break
    print('Find {} images'.format(len(files)))
    return files


crnn_model_path = './expr/best_model.pth'
alphabet = str1
nclass = len(alphabet) + 1


# crnn文本信息识别
def crnn_recognition(cropped_image, model):
    converter = utils.strLabelConverter(alphabet)

    image = cropped_image.convert('L')

    ##
    # w = int(image.size[0] / (280 * 1.0 / 160))
    transformer = dataset.resizeNormalize((192, 32))
    image = transformer(image)
    # if torch.cuda.is_available():
    #     image = image.cuda()
    image = image.view(1, *image.size())
    image = Variable(image)

    model.eval()
    preds = model(image)

    _, preds = preds.max(2)
    preds = preds.transpose(1, 0).contiguous().view(-1)

    preds_size = Variable(torch.IntTensor([preds.size(0)]))
    sim_pred = converter.decode(preds.data, preds_size.data, raw=False)
    # print('results: {0}'.format(sim_pred))
    return sim_pred


if __name__ == '__main__':
    # crnn network
    model = crnn.CRNN(32, 1, nclass, 256)
    # if torch.cuda.is_available():
    #     model = model.cuda()
    print('loading pretrained model from {0}'.format(crnn_model_path))
    # 导入已经训练好的crnn模型
    model.load_state_dict(torch.load(crnn_model_path, map_location='cpu'))

    started = time.time()
    ## read an image
    im_fn_list = get_images()
    with open(os.path.join(FLAGS.output_path, "crnn_train_result_0606.csv"),
              "a") as f:
        title ='name,label'+ "\r\n"
        f.writelines(title)
        for i, im_fn in enumerate(im_fn_list):
            if i%1000==0:
                print('.................'+str(i)+'................')
            image = Image.open(im_fn)
            result = crnn_recognition(image, model)
            line = os.path.basename(im_fn)
            # print(line,result)
            line += ',' + result + "\r\n"
            f.writelines(line)

    finished = time.time()
    print('elapsed time: {0}'.format(finished - started))
