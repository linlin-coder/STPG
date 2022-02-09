# global_sign=''
from lib.public_method import *

class GlobalPara:
    global_sign = 'tmp'
    configfile = ''
    def define_sign(self,):
        tool_config = myconf()
        tool_config.read(self.configfile)
        self.global_sign=tool_config['sign']['finish_sign']
