import os
import sys
import logging
import datetime
import json
import time
import re
import subprocess


class utils:
    """Class for File related methods """

    def script_run_time(self, seconds):
        self.seconds = seconds
        min, sec = divmod(seconds, 60)
        hrs, min = divmod(min, 60)
        timedatastring = "%d:%02d:%02d" % (hrs, min, sec)
        return timedatastring


    def check_file(self, filepath):
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            print 'File %s not found !!' % self.filepath
            print "Terminating execution now!!"
            exit()
        else:
            print 'File "%s" is present !!' % self.filepath


    def get_input_data(self,input_file):
        self.infra_file = input_file
        f = open(self.infra_file, 'r')
        try:
            data = json.load(f)
            return data
        except ValueError, e:
            print "Incorrect json format"
            print e
            exit()
        finally:
            f.close()


    def setup_custom_logger(self,name,tcStartTime,fileBaseName,inputName=""):
        self.tcStartTime = tcStartTime
        self.fileBaseName = fileBaseName
        self.inputName = inputName
        if self.inputName == "" or inputName == None:
            st = datetime.datetime.fromtimestamp(self.tcStartTime).strftime('%Y-%m-%d-%H-%M-%S')
            filename = self.fileBaseName + "-"  +  st + '.log'
            dirName = "LOGS/"
            dirPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', dirName))
            logfilename = os.path.join(dirPath, filename)
            if not os.path.isdir(dirPath):
                os.makedirs(dirPath)
        else:
            logfilename = self.inputName
        formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        handler = logging.FileHandler(logfilename,mode='w')
        handler.setFormatter(formatter)
        screen_handler = logging.StreamHandler(stream=sys.stdout)
        screen_handler.setFormatter(formatter)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.addHandler(screen_handler)
        return logger,logfilename

    def border_print(self,header_footer,msg,logger):
        self.hf,self.msg,self.logger = header_footer,msg,logger
        line = "    " + self.msg + "    "
        totalLength = len(line) + 50
        self.logger.info("")
        self.logger.info("+" * totalLength)
        self.logger.info(line.center(totalLength, "+"))
        self.logger.info("+" * totalLength)
        self.logger.info("")
        if self.hf.lower() == "footer":
            time.sleep(2)

    def inventory_info(self,inventory_dict,vm_names_list,logger):
        self.inventory_dict,self.vmnames_list,self.logger = inventory_dict,vm_names_list,logger
        self.border_print("header","Inventory info", self.logger)
        line = "Master VM Name = '" + vm_names_list[0] + "' , IP address = '" + self.inventory_dict[vm_names_list[0]] + "'"
        self.logger.info(line)
        for vm in self.vmnames_list[1:]:
            line = "Worker VM Name = '"  + vm + "' , IP address = '" + self.inventory_dict[vm] + "'"
            self.logger.info(line)



    def is_valid_ip(self,ip):
        self.ip = ip
        m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", self.ip)
        return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

    def check_cowsay(self):
        FNULL = open(os.devnull, 'w')
        cmd = "cowsay"
        try:
            subprocess.call([cmd, "-l"],stdout=FNULL, stderr=subprocess.STDOUT)
            return True
        except:
            return False

    def netmask_to_cidr(self,netmask):
        '''
        :param netmask: netmask ip addr (eg: 255.255.255.0)
        :return: equivalent cidr number to given netmask ip (eg: 24)
        '''
        self.netmask = netmask
        return sum([bin(int(x)).count('1') for x in self.netmask.split('.')])

    def update_calico(self,calico_url,pod_cidr,logger):
        self.calico_url,self.pod_cidr, self.logger = calico_url,pod_cidr, logger
        self.logger.info("Attempting to modify calico yaml")
        self.calico_yaml = "/tmp/calico.yaml"
        subprocess.call(["wget", self.calico_url, "-O",self.calico_yaml])
        sed_operation = 's/192.168.0.0\/16/' + self.pod_cidr.split("/")[0] + '\/' +  self.pod_cidr.split("/")[-1] + '/g'
        #self.logger.info(sed_operation)
        subprocess.call(["sed", "-i", sed_operation, '/tmp/calico.yaml'])
        return self.calico_yaml

if __name__ == "__main__":
    print "file_utils imported"