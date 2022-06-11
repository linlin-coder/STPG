# global_sign=''
from lib.public_method import *

class GlobalPara:
    global_sign = 'sign'
    configfile = ''
    def define_sign(self,):
        yamldict = read_yaml(self.configfile)["resource"]
        self.global_sign=yamldict['sign']['finish_sign']
