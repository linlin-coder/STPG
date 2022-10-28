import uuid
import base64
import datetime,time
# import win32api
from enum import Enum
from pyDes import *

def unix_time():
    dtime = datetime.datetime.now()
    un_time = time.mktime(dtime.timetuple())
    return int(un_time)

def get_mac_address():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e+2] for e in range(0,11,2)])

class AuthorCode(Enum):
    Author_right = 1
    Author_overtime = -1
    Author_NoneDecode = -2
    Author_NoneRegist = -3

class Authorize:
    def __init__(self,keynum="BHC#@*UM", toolbin='.'):
        self.Des_Key = keynum  # Key
        self.max_author_day = 600
        self.toolbin = toolbin
        self.Des_IV = "12345678"

    def getCVolumeSerialNumber(self):
        CVolumeSerialNumber = get_mac_address()#win32api.GetVolumeInformation("C:\\")[1]
        if CVolumeSerialNumber:
            return str(CVolumeSerialNumber)
        else:
            return 0

    def DesEncrypt(self, str):
        k = des(self.Des_Key, CBC, self.Des_IV, pad=None, padmode=PAD_PKCS5)
        # EncryptStr = k.encrypt(str)
        EncryptStr = k.encrypt(str)
        # EncryptStr = unhexlify(k.encrypt(str))
        return base64.b64encode(EncryptStr)

    def DesDecrypt(self, str):
        k = des(self.Des_Key, CBC, self.Des_IV, pad=None, padmode=PAD_PKCS5)
        DecryptStr = k.decrypt(str)
        # DecryptStr = a2b_hex(k.decrypt(str))

        return DecryptStr

    def create_code(self, mac_loc):
        serialnumber = str(mac_loc)
        serialnumberkey = self.DesEncrypt(serialnumber).decode('utf8')
        print("Registration code you created:",serialnumberkey)

    def regist(self):
        key = input('please input your register code: ')
        if key:
            content = self.getCVolumeSerialNumber()
            key_decrypted = str(self.DesDecrypt(base64.b64decode(key)).decode())
            if content != 0 and key_decrypted != 0:
                if content != key_decrypted:
                    print("wrong register code, please check and input your register code again:")

                    self.regist()
                elif content == key_decrypted:
                    print("register succeed.")
                    content += '_' + str(unix_time())
                    key = self.DesEncrypt(content).decode('utf8')
                    with open('{0}/register'.format(self.toolbin), 'w') as f:
                        f.write(key)
                        f.close()
                    return True
                else:
                    return False
            else:
                return False
        else:
            self.regist()
        return False

    def checkAuthored(self):
        content = self.getCVolumeSerialNumber()
        checkAuthoredResult = AuthorCode.Author_NoneRegist
        residueday = 0
        try:
            f = open('{0}/register'.format(self.toolbin), 'r')
            if f:
                key = f.read()
                if key:
                    key_decrypted = self.DesDecrypt(base64.b64decode(key)).decode()
                    if key_decrypted:
                        key_decrypted_mac = '_'.join(key_decrypted.split("_")[:-1])
                        key_decrypted_unitime = key_decrypted.split("_")[-1]
                        is_overtime, residueday = self.author_time_check(key_decrypted_unitime)
                        if key_decrypted_mac == content and  is_overtime:
                            checkAuthoredResult = AuthorCode.Author_right
                        else:
                            checkAuthoredResult = AuthorCode.Author_overtime
                    else:
                        checkAuthoredResult = AuthorCode.Author_NoneDecode
                else:
                    checkAuthoredResult = AuthorCode.Author_NoneRegist
            else:
                self.regist()
        except IOError:
            print(IOError)
            checkAuthoredResult = AuthorCode.Author_NoneRegist
        return checkAuthoredResult, residueday

    def author_time_check(self, authortime):
        unixnow = str(unix_time())
        dayall = delta_day(unix_human_time(authortime), unix_human_time(unixnow))
        if dayall <= self.max_author_day:
            return True, self.max_author_day - dayall
        else:
            return False, self.max_author_day - dayall

def unix_human_time(nedd):
    res = time.strftime("%Y-%m-%d", time.localtime(int(nedd[0:10])))
    return res

def _delta_day(t1, t2):
    t1 = time.mktime(time.strptime(t1, '%Y-%m-%d'))
    t2 = time.mktime(time.strptime(t2, '%Y-%m-%d'))
    delta = (t2 - t1) / 86400
    return delta

def delta_day(t1, t2):
    try:
        return _delta_day(t1, t2)
    except ValueError:
        return None

if __name__ == '__main__':
    reg = Authorize()
    reg.regist()
