# !/usr/bin/python
# -*- coding: UTF-8 -*-
import configparser
import datetime
import os,shutil
import re
import subprocess
import sys
import random, string
import yaml

bindir = os.path.realpath(os.path.dirname(__file__))

class Log():
    def __init__(self,filename,funcname=''):
        self.filename = filename
        self.funcname = funcname

    def _format(self,level,message):
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatter = ''
        if self.funcname == '':
            formatter = '\n{0} - {1} - {2} - {3} \n'.format(date_now,self.filename,level,message)
        else:
            formatter = '\n{0} - {1} - {2} - {3} - {4} \n'.format(date_now,self.filename,self.funcname,level,message)

        return formatter

    def info(self, message):
        sys.stdout.write(self._format('INFO',message=message))

    def debug(self, message):
        sys.stdout.write(self._format('DEBUG',message=message))

    def warning(self, message):
        sys.stdout.write(self._format('WARNING',message=message))

    def error(self, message):
        sys.stderr.write(self._format('ERROR',message=message))
        sys.exit(1)

    def fatal(self, message, exit_code=1):
        sys.stderr.write(self._format('fatal', message=message))
        sys.exit(exit_code)

std = Log(os.path.basename(__file__))

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
            if line.startswith('#') or not line:continue
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
                    else:
                        para[tmp[0]] = tmp[1]
                if header == 'DB':
                    tmp = [i.strip() for i in line.rstrip().split('=',1) ] 
                    if len(tmp) < 2 :
                        sys.stderr.write("Error:{0} is lack of value".format(line.rstrip()))
                        sys.exit(1)
                    else:
                        db[tmp[0]] = tmp[1]
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