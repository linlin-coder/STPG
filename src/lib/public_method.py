# !/usr/bin/python
# -*- coding: UTF-8 -*-
import configparser
import datetime
import traceback
import os
import random
import re,time
import shutil
import string
import subprocess
import sys
import colorlog
import functools
import yaml
import logging
from logging.handlers import RotatingFileHandler

from DesignMode import Singleton

bindir = os.path.realpath(os.path.dirname(__file__))
# home_path = os.path.realpath('~')
# # cur_path = os.path.dirname(os.path.realpath(__file__))  # 当前项目路径
# log_path = os.path.join(os.path.realpath(home_path), 'log')  # log_path为存放日志的路径
# if not os.path.exists(log_path): os.mkdir(log_path)  # 若不存在logs文件夹，则自动创建

log_colors_config = {
    # 终端输出日志颜色配置
    'DEBUG': 'white',
    'INFO': 'cyan',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

default_formats = {
    # 终端输出格式
    'color_format': '%(log_color)s%(asctime)s-%(name)s-%(filename)s-[line:%(lineno)d]-%(levelname)s-[日志信息]: %(message)s',
    # 日志输出格式
    'log_format': '%(asctime)s-%(name)s-%(filename)s-[line:%(lineno)d]-%(levelname)s-[日志信息]: %(message)s'
}


def get_now_time_str(format:str = '%Y-%m-%d %H:%M:%S') -> str:
    return datetime.datetime.strftime(datetime.datetime.now(),format)

def formatTime(seconds):
    if seconds < 60:
        return "{:.4f}秒".format(seconds)
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return "{}分{}秒".format(int(minutes), int(seconds))
    else:
        hours = seconds // 3600
        minutes = (seconds - hours * 3600) // 60
        seconds = seconds - hours * 3600 - minutes * 60
        return "{}小时{}分{}秒".format(int(hours), int(minutes), int(seconds))

@Singleton
class Log:
    """
    先创建日志记录器（logging.getLogger），然后再设置日志级别（logger.setLevel），
    接着再创建日志文件，也就是日志保存的地方（logging.FileHandler），然后再设置日志格式（logging.Formatter），
    最后再将日志处理程序记录到记录器（addHandler）
    """

    def __init__(self, runpyfile:str = ''):
        self.__now_time = get_now_time_str(format='%Y-%m')  # 当前日期格式化
        # self.__all_log_path = os.path.join(log_path, self.__now_time + "-all" + ".log")  # 收集所有日志信息文件
        # self.__error_log_path = os.path.join(log_path, self.__now_time + "-error" + ".log")  # 收集错误日志信息文件
        self.__logger = logging.getLogger()  # 创建日志记录器
        self.__logger.setLevel(logging.INFO)  # 设置默认日志记录器记录级别

    @staticmethod
    def __init_logger_handler(log_path):
        """
        创建日志记录器handler，用于收集日志
        :param log_path: 日志文件路径
        :return: 日志记录器
        """
        # 写入文件，如果文件超过1M大小时，切割日志文件，仅保留2个文件
        logger_handler = RotatingFileHandler(filename=log_path, maxBytes=1 * 1024 * 1024, backupCount=2, encoding='utf-8')
        return logger_handler

    @staticmethod
    def __init_console_handle():
        """创建终端日志记录器handler，用于输出到控制台"""
        console_handle = colorlog.StreamHandler()
        return console_handle

    def __set_log_handler(self, logger_handler, level=logging.DEBUG):
        """
        设置handler级别并添加到logger收集器
        :param logger_handler: 日志记录器
        :param level: 日志记录器级别
        """
        logger_handler.setLevel(level=level)
        self.__logger.addHandler(logger_handler)

    def __set_color_handle(self, console_handle):
        """
        设置handler级别并添加到终端logger收集器
        :param console_handle: 终端日志记录器
        :param level: 日志记录器级别
        """
        console_handle.setLevel(logging.DEBUG)
        self.__logger.addHandler(console_handle)

    @staticmethod
    def __set_color_formatter(console_handle, color_config):
        """
        设置输出格式-控制台
        :param console_handle: 终端日志记录器
        :param color_config: 控制台打印颜色配置信息
        :return:
        """
        formatter = colorlog.ColoredFormatter(default_formats["color_format"], log_colors=color_config)
        console_handle.setFormatter(formatter)

    @staticmethod
    def __set_log_formatter(file_handler):
        """
        设置日志输出格式-日志文件
        :param file_handler: 日志记录器
        """
        formatter = logging.Formatter(default_formats["log_format"], datefmt='%a, %d %b %Y %H:%M:%S')
        file_handler.setFormatter(formatter)

    @staticmethod
    def __close_handler(file_handler):
        """
        关闭handler
        :param file_handler: 日志记录器
        """
        file_handler.close()

    def __console(self, level, message):
        """构造日志收集器"""
        # all_logger_handler = self.__init_logger_handler(self.__all_log_path)  # 创建日志文件
        # error_logger_handler = self.__init_logger_handler(self.__error_log_path)
        console_handle = self.__init_console_handle()

        # self.__set_log_formatter(all_logger_handler)  # 设置日志格式
        # self.__set_log_formatter(error_logger_handler)
        self.__set_color_formatter(console_handle, log_colors_config)

        # self.__set_log_handler(all_logger_handler)  # 设置handler级别并添加到logger收集器
        # self.__set_log_handler(error_logger_handler, level=logging.ERROR)
        self.__set_color_handle(console_handle)

        if level == 'info':
            self.__logger.info(message)
        elif level == 'debug':
            self.__logger.debug(message)
        elif level == 'warning':
            self.__logger.warning(message)
        elif level == 'error':
            self.__logger.error(message)
        elif level == 'critical':
            self.__logger.critical(message)

        # self.__logger.removeHandler(all_logger_handler)  # 避免日志输出重复问题
        # self.__logger.removeHandler(error_logger_handler)
        self.__logger.removeHandler(console_handle)

        # self.__close_handler(all_logger_handler)  # 关闭handler
        # self.__close_handler(error_logger_handler)

    def debug(self, message):
        self.__console('debug', message)

    def info(self, message):
        self.__console('info', message)

    def warning(self, message):
        self.__console('warning', message)

    def error(self, message):
        self.__console('error', message)

    def critical(self, message):
        self.__console('critical', message)

    def logAsDecorator(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            try:
                start_time = time.time()
                aa = func(*args, **kw)
                end_time = time.time()
                self.info(
                    f"""
================================================
函数运行详情如下：
函数名称：{func.__name__}
函数入参：{args},{kw}
函数返回：{aa}
当前时间：{get_now_time_str()}
运行时间: {formatTime(end_time - start_time)}
=================================================""")
            except Exception as e:
                exception_info = traceback.format_exc()
                aa = 'err:' + str(e)
                if aa is None:
                    dretrun = ''
                elif isinstance(aa, str):
                    dretrun = aa
                elif isinstance(aa, tuple):
                    dretrun = list(aa)
                else:
                    dretrun = str(aa)
                #self.error(dretrun)
                self.error(f"Exception occurred: {dretrun}\n{exception_info}")
            return aa
        return wrapper

std = Log()

class myconf(configparser.ConfigParser):
    def __init__(self,defaults=None):
        configparser.ConfigParser.__init__(self,defaults=None,allow_no_value=True)
    def optionxform(self, optionstr):
        return optionstr

class Config():
    def __init__(self, config_file, method='', check=True):
        self.config_file = config_file
        self.method = method
        self.check_file_exist(check)
        self.config = self.read_config()

    def check_file_exist(self, check=True):
        if check and not os.path.exists(self.config_file):
            std.error('file {} not exist，please check it！！！'.format(self.config_file))

    def read_config(self):
        config = myconf()
        config.read(self.config_file)

        return config

    def all_block(self,title,head):
        return self.config[title][head]

    def return_block_list(self,title):
        try:
            data = self.config[title]
        except :
            return []
        info = {}
        for rn in data:
            info[rn] = data[rn].rstrip().split(',')
        return info

    def add_a_sector(self, title):
        self.config.add_section(title)

    def add_a_value(self, title, head, value=""):
        self.config.set(title, head, value)

    def save_msg_change(self):
        self.config.write(open(self.config_file, "w"))

# class
# get realpath
def obtain_file_realpath(one_path):
    if os.path.exists(one_path):
        return os.path.realpath(one_path)
    else:
        return None

def makedir(indir,err=1):
    if os.path.exists(indir):return
    try:
        os.makedirs(indir)
    except Exception as e:
        if os.system('mkdir -p {0}'.format(indir))!=0:
            std.error('创建目录失败：{}'.format(indir))

def copy_target_dir(source_path, target_path):
    if not os.path.exists(source_path):
        std.warning("来源目录缺失，请检测，文件拷贝失败，目录为：{0}".format(source_path))
        return
    if os.path.exists(target_path):
        std.warning("输出目录存在，即将删除，目录为：{0}".format(target_path))
        shutil.rmtree(target_path)
    shutil.copytree(source_path, target_path)

# Set operation
def set_diff_operation(list1,list2):
    set_1,set_2,set_more1,set_more2 = (),(),(),()
    set_1 = set(list1)
    set_2 = set(list2)
    #集合运算
    set_1_2 = set_1 & set_2
    set_more1 = set_1 -set_1_2
    set_more2 = set_2 -set_1_2
    return set_more1,set_more2

## get recursively downstream jobs
def get_succeeds(job,order_relation):
    recursiveSucceeds = [job]
    succeeds = []
    if job in order_relation:
        succeeds = order_relation[job]
    if len(succeeds) >0:
        for each in succeeds:
            recursiveSucceeds.extend(get_succeeds(each,order_relation))
    return recursiveSucceeds

def obtain_dir_rank(onedir, level=3, isend="/"):
    if not os.path.exists(onedir):
        return None
    if os.path.isfile(onedir):
        basedir = os.path.dirname(onedir)
        rankdir = '/'.join(basedir.split("/")[:level])+isend
    elif os.path.isdir(onedir):
        rankdir = '/'.join(onedir.split("/")[:level]) + isend
    else:
        return None
    return rankdir

def subprocess_run(cmd):
    std.info('Running command is:{0}'.format(cmd))
    back = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=1)#,timeout=1,encoding='utf-8',
    if back.returncode == 0:
        std.info('CMD:{}\texecute success'.format(cmd))
        return back.stdout
    else:
        std.error('CMD:{}\texecute failed !!!'.format(cmd))
    return back

def read_yaml(files):
    with open(files, "r") as f:
        cfg = f.read()
        config = yaml.load(cfg, Loader=yaml.SafeLoader)
        #print(config)
        return(config)

class Yaml2Object:
    def __init__(self, yamlfile:str, target :str=""):
        self.yamldict = {}
        self.yamlfile = yamlfile
        self.target = target

    @property
    def parseryaml(self):
        self.yamldict = read_yaml(self.yamlfile)
        yamlObject = self.solution(self.yamldict[self.target])
        return yamlObject

    def solution(self, yamldict):
        """
        采用递归，将所有dict对象转换为Object对象
        :return:
        """
        if not yamldict or not isinstance(yamldict, dict):
            return yamldict
        for key, value in yamldict.items():
            value = self.solution(value)
            yamldict[key] = value
        yamlobject = Dict2Obj(yamldict)
        return yamlobject


class Dict2Obj(object):
    """将一个字典转换为类"""

    def __init__(self, dictionary):
        """Constructor"""
        for key in dictionary:
            setattr(self, key, dictionary[key])

    def __repr__(self):
        """print 或str 时，让实例对象以字符串格式输出"""
        return "<Dict2Obj: %s>" % self.__dict__
    
def ReadConfig(file_list):
    pat = re.compile('\[(\S+)\]')
    record = {}
    para = {}
    db = {}
    header = ''
    count = {} 
    s_index = {} ## to record table occurence time 
    for infile in file_list:
        # f_file=open(infile)
        with open(infile, 'r', encoding='utf-8') as f_config:
            f_file = f_config.readlines()
        for line in f_file:
            line=line.strip()
            if line.startswith('#') or not line or line.startswith(";"):continue
            elif line.startswith('['):
                match = pat.search(line)
                if match :
                    header = match.group(1)
                    if header not in count : 
                        count[header] = 0
                        record[header] = []
                        s_index[header] = []
                    else:
                        count[header] += 1
            else:
                if header == 'Para':
                    tmp = [i.strip() for i in line.rstrip().split('=',1) ]
                    if len(tmp) < 2 :
                        sys.stderr.write("Error:{0} is lack of value".format(line.rstrip()))
                        sys.exit(1)
                    elif len(tmp) == 2:
                        para[tmp[0]] = tmp[1]
                    else:
                        para[tmp[0]] = [tmp[0]]
                if header == 'DB':
                    tmp = [i.strip() for i in line.rstrip().split('=',1) ] 
                    if len(tmp) < 2 :
                        sys.stderr.write("Error:{0} is lack of value".format(line.rstrip()))
                        sys.exit(1)
                    elif len(tmp) == 2:
                        db[tmp[0]] = tmp[1]
                    else:
                        db[tmp[0]] = tmp[0]
                else:
                    tmp =  [i.strip() for i in re.split('[=\t]',line) ]#line.rstrip().split('=',1) ]#line.rstrip().split('\t')
                    record[header].append(tmp)
                    s_index[header].append(count[header])
        # f_file.close()
    # print(record)
    return record,para,db,s_index

class multidict(dict):
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self,item)
        except KeyError:
            value = self[item] = type(self)()
            return value

    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

def random_strings(StrNum):
    stringrandom = ''.join(random.sample(string.ascii_letters + string.digits, StrNum))
    return stringrandom

def get_user_name():
    user_name = getpass.getuser()
    return user_name
