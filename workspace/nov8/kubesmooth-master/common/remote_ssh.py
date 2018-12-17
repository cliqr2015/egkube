import paramiko
import time
import re



class remote_ssh:
    """Class for remote ssh commands"""

    def __init__(self, VMip, VMuser, authType,logger,VMpassword="",pkeyfilePath=""):
        self.VMip = VMip
        self.VMuser = VMuser
        self.auth_type = authType
        self.logger = logger
        self.VMpassword = VMpassword
        self.pkeyfilePath = pkeyfilePath
        #self.logger.info("class remote_ssh_utils has been instantiated")


    def remote_ssh_command_exec(self,cmd):
        self.cmd = cmd
        ssh = paramiko.SSHClient()
        if self.auth_type.lower() == "pw":
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.VMip, username=self.VMuser, password=self.VMpassword, key_filename='/dev/null',timeout=120)
        elif self.auth_type.lower() == "pk":
            self.cmd = "sudo -i " + cmd
            pkey = paramiko.RSAKey.from_private_key_file(self.pkeyfilePath)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.VMip, username=self.VMuser, pkey=pkey,timeout=10)
        std_in, std_out, std_err = ssh.exec_command(self.cmd)
        std_out.channel.recv_exit_status()
        return std_out.readlines()


    def remote_file_transfer_sftp(self,localpath,remotepath,mode):
        self.logger.debug("File " +  mode + " in progress ...")
        port = 22
        self.localpath,self.remotepath,self.mode = localpath,remotepath,mode
        transport = paramiko.Transport(self.VMip, port)
        if self.auth_type.lower() == "pw":
            transport.connect(username=self.VMuser, password=self.VMpassword)
        if self.auth_type.lower() == "pk":
            pkey = paramiko.RSAKey.from_private_key_file(self.pkeyfilePath)
            transport.connect(username=self.VMuser, pkey=pkey)
        transport.use_compression()
        sftp = paramiko.SFTPClient.from_transport(transport)
        if self.mode == "upload":
            sftp.put(self.localpath, self.remotepath)
            sftp.close()
        elif self.mode == "download":
            sftp.get(self.remotepath, self.localpath)
            sftp.close()
        transport.close()
        return True


    def reboot_machine(self):
        self.logger.debug("Reset network manager")
        self.remote_ssh_command_exec("systemctl restart NetworkManager")
        self.logger.info("System Reboot Initiated ...")
        self.remote_ssh_command_exec("reboot")
        time.sleep(5)
        self.logger.debug("After 5 sec wait")
        #return 1

    def check_connection(self):
        flag = 1
        while flag:
            try:
                self.logger.debug("Checking VM connection for ip " + self.VMip)
                self.remote_ssh_command_exec("ls")
                return True
            except:
                self.logger.debug("VM is still not up. Waiting for 5 seconds")
                time.sleep(5)
        return False

    def display_cmd_output(self, cmd, headermsg):
        self.cmd,self.headermsg = cmd,headermsg
        self.logger.debug(self.headermsg)
        self.logger.debug(">>> cmd executed = " + self.cmd)
        out = self.remote_ssh_command_exec(self.cmd)
        logging = [self.logger.info(line.strip()) for line in out]
        return  True

    def kube_adm_init(self, cmd, headermsg,logger):
        self.logger = logger
        self.cmd = cmd
        self.headermsg = headermsg
        self.logger.debug(self.headermsg)
        self.logger.debug(">>>> cmd executed = " + self.cmd)
        out = self.remote_ssh_command_exec(self.cmd)
        logging = [self.logger.debug(line.strip()) for line in out]
        for line in out:
            if "kubeadm join" in line:
                return line.strip()

        return -1

    def kube_join_cmd(self, cmd, headermsg):
        self.cmd,self.headermsg = cmd,headermsg
        self.logger.debug(self.headermsg)
        self.logger.debug(">>>> cmd executed = " + self.cmd)
        out = self.remote_ssh_command_exec(self.cmd)
        logging = [self.logger.debug(line.strip()) for line in out]
        for line in out:
            if "kubeadm join" in line:
                return line.strip()

        return -1

    def check_tiller(self):
        self.logger.info("Tiller verification...")
        self.cmd = "kubectl get pod --all-namespaces| grep tiller"
        #out = self.remote_ssh_command_exec(self.cmd)
        tiller_not_ready = False
        poll_count = 0
        while not tiller_not_ready:
            out = self.remote_ssh_command_exec(self.cmd)
            for line in out:
                if "1/1" in line.strip() and "Running" in line.strip():
                    tiller_not_ready = True
                    return tiller_not_ready
                else:
                    logging = [self.logger.info(line.strip()) for line in out]
                    self.logger.info("Waiting 30 sec for tiller pods to come up...")
                    self.logger.info("Poll Count => " + str(poll_count))
                    time.sleep(30)
            poll_count = poll_count + 1
            if poll_count > 10:
                break

        return tiller_not_ready

    def pod_display(self):
        msg ="Pod status across all namespaces"
        line = "    " + msg + "    "
        totalLength = len(line) + 50
        self.logger.info("")
        self.logger.info("+" * totalLength)
        self.logger.info(line.center(totalLength, "+"))
        self.logger.info("+" * totalLength)
        self.logger.info("")
        cmd = "kubectl get pod --all-namespaces -o wide"
        out = self.remote_ssh_command_exec(cmd)
        logging = [self.logger.info(line.strip()) for line in out]
        time.sleep(15)




