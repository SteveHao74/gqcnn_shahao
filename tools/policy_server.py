'''
Author: your name
Date: 2021-04-15 10:53:34
LastEditTime: 2021-04-25 13:42:14
LastEditors: Please set LastEditors
Description: In User Settings Edit
FilePath: /shahao_gq/tools/policy_server.py
'''
import sys
import os
import argparse
import Pyro4
import random
import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from ruamel.yaml import YAML


file_path = os.path.split(__file__)[0]
ROOT_PATH = os.path.abspath(os.path.join(file_path, '..'))
sys.path.append(os.path.join(ROOT_PATH, 'src'))
try:
    from easygqcnn import GraspingPolicy
except Exception as e:
    raise e
TEST_LOG_FILE = os.path.join(ROOT_PATH, 'tools/logs/policy_visual.log')
TEST_CFG_FILE = os.path.join(ROOT_PATH, 'config/policy.yaml')
IMAGE = os.path.join(ROOT_PATH, 'data/test/depth.npy')
GMDATA_PATH = Path.home().joinpath('Project/gmdata')
MODEL_PATH = GMDATA_PATH.joinpath('datasets/models/gq/small_data')

# TRAIN_DATA_PATH = GMDATA_PATH.joinpath('datasets/train_datasets/gq_data/small_data_train')


def config_logging(file=None, level=logging.DEBUG):
    """ 配置全局的日志设置 """
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=file, level=level,
                        format=LOG_FORMAT, filemode='w')


def load_config(file):
    """ 加载配置文件 """
    yaml = YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
    with open(file, 'r', encoding="utf-8") as f:
        config = yaml.load(f)
    return config


@Pyro4.expose
class Planer(object):
    def __init__(self, config):
        # config = load_config(TEST_CFG_FILE)
        # config['gqcnn_config']['model_path'] = model_path
        # config_logging(TEST_LOG_FILE)
        self.policy = GraspingPolicy(config)
        print('ok')

    def plan(self, image, width):
        random.seed(0)
        np.random.seed(0)
        im = image.copy()
        try_num = 5
        qs = []
        gs = []
        for _ in range(try_num):
            try:
                g, q = self.policy.action(im, None, width=width, g_depth=0)
            except Exception as e:
                print('--------------------出错了----------------------')
                print(e)
            else:
                qs.append(q)
                gs.append(g)
                if q > 0.9:
                    break
        if len(gs) == 0:
            return None
        g = gs[np.argmax(qs)]
        q = qs[np.argmax(qs)]
        p0, p1 = g.endpoints
        print(p0, p1, g.depth, g.depth, q)
        return [p0, p1, g.depth, g.depth, q]


def main(args):
    model_path = MODEL_PATH.joinpath(args.model_name)
    config = load_config(TEST_CFG_FILE)
    config['gqcnn_config']['model_path'] = model_path.as_posix()
    pp = Planer(config)
    Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')
    Pyro4.Daemon.serveSimple({pp: 'grasp'}, ns=False, host='', port=6665)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='dataset to npz')
    parser.add_argument('-m', '--model-name', metavar='gmd', type=str, default='gmd',
                        help='使用的模型的名字')
    args = parser.parse_args()
    main(args)
