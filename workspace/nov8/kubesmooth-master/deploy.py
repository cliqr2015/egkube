print "\033c"  # Clears screen on Cygwin Console

import os
import sys
import argparse
import time
import datetime
import uuid
import atexit
from pyVim.connect import SmartConnectNoSSL, Disconnect
import subprocess
import platform


def init():
    timeStamp = datetime.datetime.fromtimestamp(tcStartTime).strftime('%Y%m%d%H%M%S')
    fileBaseName = os.path.basename(__file__).split(".")[0]
    folder_names = ['common','constants','tasks']
    for file in folder_names:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '', file)))
    return timeStamp,fileBaseName



tcStartTime = time.time()
parser = argparse.ArgumentParser(description='Borg me up !!')
parser.add_argument('-i','--input', dest='input_file', type=str, help='Input json file path',required=True)
args = parser.parse_args()
timeStamp,fileBaseName = init()
from remote_ssh import *
from utils import *
from vmware_utils import *
from constants import *
from taskList import *


file_util = utils()
logger, logFileName = file_util.setup_custom_logger("Borg setup", tcStartTime, fileBaseName)
file_util.check_file(args.input_file)
stamp = datetime.datetime.fromtimestamp(tcStartTime).strftime('%Y%m%d%H%M%S')
const = constants()
logger.info("Reading input file %s" % args.input_file)
data = file_util.get_input_data(args.input_file)


vcenter_ip = data['vcenter-server']
vcenter_user = data['vcenter-user']
vcenter_password = data['vcenter-password']
vm_username = data['ssh_creds']['username']
vm_password = data['ssh_creds']['password']
api_auth_type = data['ssh_creds']['authentication_type']
number_of_vms = data['numberOfVMs']
vm_name_prefix = data['vm_name_prefix']
vm_template_name = data['vm_template_details']['template_name']
datastore_name = data['vm_template_details']['datastoreName']
port_group_name_list = data['customization_data']['networkList']
num_cpu = data['vm_template_details']['vcpu']
memory_gb = data['vm_template_details']['ramGb']
vcenter_resource_pool = data['vm_template_details']['resourcePool']
customization = data['customization_flag']
vm_ip_list = data['customization_data']['ipList']
vm_subnet_mask_list = data['customization_data']['subnetMaskList']
vm_gateway_list = data['customization_data']['gatewayList']
vm_dns_list = data['customization_data']['dnsList']
vm_domain = data['customization_data']['domainName']
nfs_server = data["nfs_server"]
nfs_path = data["nfs_path"]
nfs_deploy = data['deploy_nfs']
nfs_customization = data['nfs_details']['customization_flag']
nfs_vm_ip = data['nfs_details']['ipList']
nfs_vm_subnet_mask = data['nfs_details']['subnetMaskList']
nfs_vm_gateway = data['nfs_details']['gatewayList']
nfs_vm_dns = data['nfs_details']['dnsList']
nfs_pg = data['nfs_details']['networkList']
nfs_vm_domain = data['nfs_details']['domainName']
nfs_subnet = data["nfs_details"]["nfs_subnet"]
pod_cidr = data["pod_cidr"]
kube_user = data["kube-user"]
BASE_PATH = "/root/kube-users/"
CA_LOCATION = "/etc/kubernetes/pki"
USER_KUBECONFIG = kube_user + "-kubeconfig"
DASHBOARD_TEMPLATE = "dashboard-rolebind-user.yaml"
TILLER_TEMPLATE = "tiller-rolebind.yaml"
RESULTS_DIR = data["resultDir"]

print ""
cowsay = False
if file_util.check_cowsay():
    logger.info(subprocess.call(["cowsay", "-f", "tux", "Starting execution"]))
    cowsay = True
else:
    try:
        FNULL = open(os.devnull, 'w')
        if platform.dist()[0].lower() == const.ubuntu:
            subprocess.call(["apt", "install", "cowsay", "-y"],stdout=FNULL, stderr=subprocess.STDOUT)
        if platform.dist()[0].lower() == const.centos:
             subprocess.call(["yum", "install", "cowsay", "-y"],stdout=FNULL, stderr=subprocess.STDOUT)
        logger.debug("Cowsay was installed successfully ..")
        print ""
        logger.info(subprocess.call(["cowsay", "-f", "tux", "So much work to do now"]))
        cowsay = True
    except:
        logger.info("Skipping cowsay install ..")
print ""


def border_print(msg, logger):
    line = "    " + msg + "    "
    totalLength = len(line) + 50
    logger.info("")
    logger.info("+" * totalLength)
    logger.info(line.center(totalLength, "+"))
    logger.info("+" * totalLength)
    logger.info("")

def create_user(vmhandle,username,user_path,cert_path,logger):
    border_print("Creating User '" + username + "' on API server '" + str(vmhandle.VMip) + "'",logger)
    full_user_path = user_path  + username
    vmhandle.display_cmd_output("mkdir -p " + full_user_path + "/.certs","Creating directory => " + full_user_path)
    full_user_path = full_user_path + "/" + kube_user
    vmhandle.display_cmd_output("openssl genrsa -out " + full_user_path + ".key 2048", "Creating key => " + full_user_path + ".key")
    vmhandle.display_cmd_output('openssl req -new -key ' + full_user_path + '.key -out ' + full_user_path + '.csr -subj  "/CN=' + username + '/O=cisco"',"Creating csr => " + full_user_path + ".csr")
    vmhandle.display_cmd_output("openssl x509 -req -in " + full_user_path + ".csr -CA " + cert_path + "/ca.crt -CAkey " + cert_path + "/ca.key -CAcreateserial -out " + full_user_path + ".crt -days 1000", "Creating x509 cert  => " + full_user_path + ".crt")
    #vmhandle.display_cmd_output("mv " + full_user_path + ".key " + user_path  + username + "/.certs/", "Moving keys")
    #vmhandle.display_cmd_output("mv " + full_user_path + ".csr " + user_path  + username + "/.certs/","Moving certs")

def create_namespace(vmhandle,username,logger):
    border_print("Creating Namespace for '" + username + "' on API server '" + str(vmhandle.VMip) + "'", logger)
    vmhandle.display_cmd_output("kubectl create namespace " + username, "Creating namespace " + username)


def generate_user(vmhandle,username,user_path,ip,logger):
    full_user_path = user_path + username + "/" + username
    kube_config_file_path = full_user_path + "-kubeconfig"
    kube_api_server = "https://" + ip + ":6443"
    border_print("Creating kubeconfig  for '" + username + "' on API server '" + str(vmhandle.VMip) + "'", logger)
    vmhandle.display_cmd_output("kubectl config set-credentials " + username + " --client-certificate=" + full_user_path + ".crt --client-key=" + full_user_path + ".key --embed-certs=true --kubeconfig " + kube_config_file_path, "Setting kubeconfig creds")
    vmhandle.display_cmd_output("kubectl config set-cluster kubernetes --server=" + kube_api_server + " --insecure-skip-tls-verify=true --kubeconfig " +  kube_config_file_path, "Setting kubeconfig creds api server ")
    vmhandle.display_cmd_output("kubectl config set-context " + username + "-context --cluster=kubernetes --namespace=" + username + " --user=" + username + " --kubeconfig "  + kube_config_file_path, "Setting kubeconfig context")
    vmhandle.display_cmd_output("kubectl config use-context " + username + "-context --kubeconfig " + kube_config_file_path, "Using kubeconfig context")


def create_rbac(vmhandle,username,logger):
    border_print("Creating RBAC rules  for '" + username + "' on API server '" + str(vmhandle.VMip) + "'", logger)
    vmhandle.display_cmd_output(
        "kubectl create rolebinding " + username + "-role-binding01 --clusterrole=cluster-admin --user " + username + " --namespace=" + username, "Create RBAC Role Binding User namespace")
    ###Needed fkube-system access
    vmhandle.display_cmd_output(
        "kubectl create rolebinding " + username + "-role-binding02 --clusterrole=cluster-admin --user " + username + " --namespace=kube-system" , "Create RBAC Role Binding Kube-system namespace")

    ###Needed for CCO registration and dashboard
    vmhandle.display_cmd_output("kubectl create clusterrolebinding tiller-rb --clusterrole=cluster-admin --user=" + username + " --serviceaccount=" + username + ":default", "Create RBAC Cluster Role Binding 1")
    #vmhandle.display_cmd_output(
    #    "kubectl create clusterrolebinding crb2 --clusterrole=cluster-admin --user=" + username + " --serviceaccount=" + username + ":kube-system","Create RBAC Cluster Role Binding 2")





def run_tasks(kubeconfpath):
    task = taskList()
    if len(task.taskdata) > 0:
        for k, v in task.taskdata.items():
            file_util.border_print("header", "Running Task : " + k, logger)
            cmd = "export KUBECONFIG=" + kubeconfpath + ";" + v
            vmhandle_master.display_cmd_output(cmd, k)
            time.sleep(5)


vm_names_list = []
appliance_info_dict = {}
for i in range(number_of_vms):
    if i ==0 :
        vmName = vm_name_prefix + "-master-" + str(uuid.uuid4())[:4]
    else:
        vmName = vm_name_prefix + "-" + str(uuid.uuid4())[:6]
    vm_names_list.append(vmName)

if nfs_deploy.lower() == const.bool_true:
    nfs_vm_name = "nfs-" + vm_name_prefix + "-" + str(uuid.uuid4())[:6]
    vm_names_list.append(nfs_vm_name)
    vm_ip_list.append(nfs_vm_ip[0])
    vm_subnet_mask_list.append(nfs_vm_subnet_mask[0])
    vm_gateway_list.append(nfs_vm_gateway[0])
    vm_dns_list.append(nfs_vm_dns[0])
    port_group_name_list.append(nfs_pg[0])

#validations
if not file_util.is_valid_ip(vcenter_ip):
    logger.info("Invalid vcenter ip address detected => ", vcenter_ip)
    exit()

vcenter = vmware_utils(vcenter_ip,vcenter_user,vcenter_password,logger)
si = vcenter.vcenter_connect()
atexit.register(Disconnect, si)

if customization.lower() == const.bool_true:
    vcenter.vmware_create_vm(si,vm_names_list,vm_template_name, vm_ip_list, vm_subnet_mask_list, vm_gateway_list, vm_dns_list, const.static_ip , datastore_name, vm_domain,
                         vcenter_resource_pool,port_group_name_list,num_cpu,memory_gb)

else:
    vcenter.vmware_create_vm(si,vm_names_list, vm_template_name, vm_ip_list, vm_subnet_mask_list, vm_gateway_list,
                             vm_dns_list, const.dhcp, datastore_name, vm_domain,
                             vcenter_resource_pool, port_group_name_list, num_cpu, memory_gb)




#vm_names_list = ['abmitra-master-b928']

file_util.border_print("header","Fetching IP address of all VM's",logger)

for i in range(len(vm_names_list)):
    logger.info("Fetching Ip Address of VM => " + vm_names_list[i])
    appliance_ip = vcenter.get_vm_ipaddr(si, vm_names_list[i])
    while appliance_ip == None:
        logger.warning("Invalid IP detected. Retrying after 60 seconds")
        time.sleep(60)
        appliance_ip = vcenter.get_vm_ipaddr(si, vm_names_list[i])
    logger.info("IP Address of VM " + vm_names_list[i] + " : " + appliance_ip)
    appliance_info_dict[vm_names_list[i]] = appliance_ip


vcenter.vcenter_disconnect(si)

vmhandle_master = remote_ssh(appliance_info_dict[vm_names_list[0]], vm_username, api_auth_type,logger,vm_password)


file_util.border_print("header","Kubeadm init",logger)
if pod_cidr != "":
    kubeadminit_cmd = "kubeadm init --pod-network-cidr=" + str(pod_cidr)
else:
    pod_cidr = "192.168.0.0/16"
    kubeadminit_cmd = "kubeadm init --pod-network-cidr=" + str(pod_cidr)
vmhandle_master.display_cmd_output(kubeadminit_cmd,"Initializing kubeadm int on master " + vm_names_list[0])
file_util.border_print("header","Generate join string",logger)
join_string = vmhandle_master.kube_join_cmd("kubeadm token create --print-join-command","Generating token on master " + vm_names_list[0])
if join_string == -1:
    logger.error("Join string not found !")
    exit()

if nfs_deploy.lower() == const.bool_true:
    for vm in vm_names_list[1:-1]:
        vmhandle = remote_ssh(appliance_info_dict[vm], vm_username, api_auth_type, logger, vm_password)
        file_util.border_print("header", "VM '" + vm + "' joining master '" + vm_names_list[0] + "'", logger)
        vmhandle.display_cmd_output(join_string, vm + " joining k8 master")
        del vmhandle
else:
    for vm in vm_names_list[1:]:
        vmhandle = remote_ssh(appliance_info_dict[vm], vm_username, api_auth_type,logger,vm_password)
        file_util.border_print("header", "VM '" + vm + "' joining master '" + vm_names_list[0] + "'", logger)
        vmhandle.display_cmd_output(join_string,vm + " joining k8 master")
        del vmhandle

file_util.border_print("header","Setting up kubectl on master '" + vm_names_list[0] + "'",logger)
kubectl_init_cmd_list = ["mkdir -p $HOME/.kube",
                         "sudo cp  /etc/kubernetes/admin.conf $HOME/.kube/config",
                         "sudo chown $(id -u):$(id -g) $HOME/.kube/config"]
op_list = [vmhandle_master.display_cmd_output(cmd,"CMD = " + cmd) for cmd in kubectl_init_cmd_list]

file_util.border_print("header","Node status",logger)
vmhandle_master.display_cmd_output("kubectl get nodes","K8 node status")

file_util.border_print("header","Deploying calico network addon",logger)
calico_url = "https://docs.projectcalico.org/v3.3/getting-started/kubernetes/installation/hosted/kubernetes-datastore/calico-networking/1.7/calico.yaml"
#weave_cmd = 'kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d' + "'\n')" + '"'
calico_cmd_1 = "kubectl apply -f https://docs.projectcalico.org/v3.3/getting-started/kubernetes/installation/hosted/rbac-kdd.yaml"
calico_cmd_2 = "kubectl apply -f " + calico_url


#vmhandle.display_cmd_output(weave_cmd,"Installing Weave",logger)
vmhandle_master.display_cmd_output(calico_cmd_1,"Deploying Calico accounts")

calico_url = "https://docs.projectcalico.org/v3.3/getting-started/kubernetes/installation/hosted/kubernetes-datastore/calico-networking/1.7/calico.yaml"
if pod_cidr != "":
    calico_yaml_path = file_util.update_calico(calico_url,pod_cidr,logger)
    status = vmhandle_master.remote_file_transfer_sftp(calico_yaml_path, "/tmp/calico.yaml", "upload")
    vmhandle_master.display_cmd_output("kubectl apply -f /tmp/calico.yaml", "Deploying Calico")
else:
    vmhandle_master.display_cmd_output(calico_cmd_2,"Deploying Calico ")


file_util.border_print("header","Node status After Calico addon",logger)
vmhandle_master.display_cmd_output("kubectl get nodes","K8 node status after calico addon")
file_util.border_print("header","All Pod Status",logger)
vmhandle_master.pod_display()


if nfs_deploy.lower() == const.bool_true:
    file_util.border_print("header","Setting up the NFS Server :'" + nfs_vm_name + "' and ip address: " + appliance_info_dict[nfs_vm_name] + "'" ,logger)
    vmhandle_nfs = remote_ssh(appliance_info_dict[nfs_vm_name], vm_username, api_auth_type,logger,vm_password)
    vmhandle_nfs.display_cmd_output("mkdir /root/PVC","Creating PVC folder")
    vmhandle_nfs.display_cmd_output("chown +x /root/PVC ","Giving root Permissions")
    perms = "(rw,sync,no_root_squash,no_subtree_check)"
    line = '"/root/PVC    ' + nfs_subnet + perms + '"'
    cmd = "echo " + line + ">> /etc/exports"
    vmhandle_nfs.display_cmd_output(cmd,"Exporting NFS directories")
    vmhandle_nfs.display_cmd_output("systemctl restart nfs-kernel-server","Restarting NFS Server")
    vmhandle_nfs.display_cmd_output("systemctl enable nfs-kernel-server", "Enabling NFS Server")
    del vmhandle_nfs


file_util.border_print("header","Setting up Helm",logger)
vmhandle_master.display_cmd_output("helm init","Initializing Tiller")
vmhandle_master.display_cmd_output("kubectl create clusterrolebinding cluster-rb-deploy1 --clusterrole=cluster-admin --serviceaccount=kube-system:default","Creating cluster role binding1")



file_util.border_print("header","Check tiller status",logger)
if not vmhandle_master.check_tiller():
    logger.info("Tiller has not come up yet. Please check setup as helm commands may fail otherwise")
else:
    logger.info("Tiller is running")

vmhandle_master.pod_display()


file_util.border_print("header","Cert manager install",logger)
vmhandle_master.display_cmd_output("helm install --name cert-manager stable/cert-manager","installing cert manager")
time.sleep(10)

file_util.border_print("header","NfS Provisioner install",logger)
random_id = str(uuid.uuid4())[:6]
nfs_release_name = "nfs-" +  random_id
nfs_service_account_name = "nfs-svc-acc-" + random_id
nfs_client_provisioner_name = "nfsclientprov/nfs"
nfs_storage_class_name = "nfs-storage-class-" + random_id
if nfs_deploy.lower() == const.bool_true:
    nfs_server = appliance_info_dict[nfs_vm_name]
nfs_command = "helm install --name " + str(nfs_release_name) + " --set nfs.server=" + str(nfs_server) + ",nfs.path=" + str(nfs_path) +  ",replicaCount=" + str(number_of_vms) \
              + ",storageClass.name=" + str(nfs_storage_class_name) + ",storageClass.defaultClass=true,rbac.create=true,storageClass.provisionerName=" + \
               str(nfs_client_provisioner_name) + ",serviceAccount.create=true,serviceAccount.name=" + str(nfs_service_account_name) + " stable/nfs-client-provisioner"
#print nfs_command
vmhandle_master.display_cmd_output(nfs_command,"Enabling nfs dynamic provisioner")
time.sleep(10)

file_util.border_print("header","Helm status for 'kube-system' namespace",logger)
vmhandle_master.display_cmd_output("helm ls","Helm ls")
time.sleep(10)

vmhandle_master.pod_display()

file_util.border_print("header","Creating and generating cisco user",logger)
create_user(vmhandle_master,kube_user, BASE_PATH, CA_LOCATION, logger)
create_namespace(vmhandle_master, kube_user, logger)
generate_user(vmhandle_master,kube_user,BASE_PATH, appliance_info_dict[vm_names_list[0]], logger)
create_rbac(vmhandle_master,kube_user,logger)


full_user_path = BASE_PATH + kube_user + "/" + kube_user
kube_config_file_path = full_user_path + "-kubeconfig"

file_util.border_print("header","Setting up tiller for cisco",logger)
cmd = "export KUBECONFIG=" + kube_config_file_path + ";" + "kubectl create sa prod-mgmt-tiller-account;" + \
    "kubectl create secret docker-registry suite-image-pull-secret --docker-username=multicloudsuite.gen " \
    "--docker-password=AKCp5aTvLmuvA2d1eRkiehsSAySuWZiyEv76bczZWzHe7bq5W96drHsmUzKus6v2ZsYXqMFje --docker-email=suite@cisco.com " \
    "--docker-server=devhub-docker.cisco.com;" + "helm init --tiller-namespace cisco;" + \
    "helm init --service-account  prod-mgmt-tiller-account --tiller-namespace cisco --upgrade;"
vmhandle_master.display_cmd_output(cmd,"Setting up tiller")
status = vmhandle_master.remote_file_transfer_sftp(const.tiller_rb_cisco_yaml,"/tmp/tiller-rb-cisco.yaml", "upload")
vmhandle_master.display_cmd_output("kubectl create -f /tmp/tiller-rb-cisco.yaml", "Create Tiller rolebind")
vmhandle_master.display_cmd_output("rm -rf /tmp/tiller-rb-cisco.yaml", "Cleaning up")

### Running tasks if provided

kube_config_admin_path = "/etc/kubernetes/admin.conf"
kube_config_cisco_path = "/root/kube-users/cisco/cisco-kubeconfig"
run_tasks(kube_config_cisco_path)

file_util.inventory_info(appliance_info_dict,vm_names_list,logger)
if RESULTS_DIR == "":
    RESULTS_DIR = "/root/deploy-results/" + stamp

if os.path.exists(RESULTS_DIR):
    logger.info("Results folder '%s' exists", RESULTS_DIR)
else:
    logger.info("Creating results folder '%s'", RESULTS_DIR)
    #vmhandle_master.display_cmd_output("mkdir " + RESULTS_DIR, "Creating results folder " + RESULTS_DIR)
    subprocess.call(["mkdir", "-p" ,RESULTS_DIR])

RESULTS_DIR = RESULTS_DIR + "/" + stamp
subprocess.call(["mkdir", "-p", RESULTS_DIR])
kubeconfadminpath = RESULTS_DIR + "/kubeconf-admin-" + str(uuid.uuid4())[:6]
kubeconfciscopath = RESULTS_DIR + "/kubeconf-cisco-" + str(uuid.uuid4())[:6]
status1 = vmhandle_master.remote_file_transfer_sftp(kubeconfadminpath,const.kubeadminconf, "download")
status2 = vmhandle_master.remote_file_transfer_sftp(kubeconfciscopath,kube_config_cisco_path, "download")
logger.info("")
logger.info("Admin Kubeconf File :==> " + kubeconfadminpath)
logger.info("Cisco Kubeconf File :==> " + kubeconfciscopath)
logger.info("Log File :==> " + logFileName)
logger.info("")
elapsed_time_secs = time.time() - tcStartTime
msg = "Execution time = "  + file_util.script_run_time(elapsed_time_secs)
file_util.border_print("footer",msg,logger)
del vmhandle_master


print ""
if cowsay:
    logger.info(subprocess.call(["cowsay", "-f", "ghostbusters", "Awesome, Execution Complete"]))
print ""
