import sys
import time
from pyVim.connect import SmartConnectNoSSL, Disconnect
from pyVmomi import vim


class vmware_utils:

    vcenterconnection = ""

    def __init__(self, vcenter_ip, vcenter_user, vcenter_password, logger,vcenter_port=443):
        self.vcip = vcenter_ip
        self.user = vcenter_user
        self.password = vcenter_password
        self.vcenter_port = vcenter_port
        self.logger = logger


    def _get_obj(self, content, vimtype, name):
        """
        Get the vsphere object associated with a given text name
        """
        obj = None
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            # print c.name
            if c.name == name:
                obj = c
                break
        return obj

    def _get_all_objs(self, content, vimtype):
        """
        Get all the vsphere objects associated with a given type
        """
        obj = {}
        # print content.rootFolder
        # print vimtype
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            obj.update({c: c.name})
        return obj

    def login_in_guest(self, username, password):
        return vim.vm.guest.NamePasswordAuthentication(username=username, password=password)

    def start_process(self, si, vm, auth, program_path, args=None, env=None, cwd=None):
        cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args, programPath=program_path, envVariables=env,
                                                          workingDirectory=cwd)
        cmdpid = si.content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=auth, spec=cmdspec)
        return cmdpid

    def is_ready(self, vm):

        while True:
            system_ready = vm.guest.guestOperationsReady
            system_state = vm.guest.guestState
            system_uptime = vm.summary.quickStats.uptimeSeconds
            if system_ready and system_state == 'running' and system_uptime > 90:
                break
            time.sleep(10)

    def get_vm_by_name(self, si, name):
        """
        Find a virtual machine by it's name and return it
        """
        return self._get_obj(si.RetrieveContent(), [vim.VirtualMachine], name)

    def get_host_by_name(self, si, name):
        """
        Find a virtual machine by it's name and return it
        """
        return self._get_obj(si.RetrieveContent(), [vim.HostSystem], name)

    def get_resource_pool(self, si, name):
        """
        Find a virtual machine by it's name and return it
        """
        return self._get_obj(si.RetrieveContent(), [vim.ResourcePool], name)

    def get_resource_pools(self, si):
        """
        Returns all resource pools
        """
        return self._get_all_objs(si.RetrieveContent(), [vim.ResourcePool])

    def get_datastores(self, si):
        """
        Returns all datastores
        """
        return self._get_all_objs(si.RetrieveContent(), [vim.Datastore])

    def get_datastore_by_name(self, si, name):
        """
        Returns all datastores
        """
        return self._get_obj(si.RetrieveContent(), [vim.Datastore], name)

    def get_hosts(self, si):
        """
        Returns all hosts
        """
        return self._get_all_objs(si.RetrieveContent(), [vim.HostSystem])

    def get_datacenters(self, si):
        """
        Returns all datacenters
        """
        return self._get_all_objs(si.RetrieveContent(), [vim.Datacenter])

    def get_registered_vms(self, si):
        """
        Returns all vms
        """
        return self._get_all_objs(si.RetrieveContent(), [vim.VirtualMachine])


    def WaitTask(self, taskList, actionName='job', sleeptime=30):
        self.taskList, self.actionName, self.sleeptime = taskList, actionName, sleeptime

        done = 0
        taskDoneFlagList = []
        taskCompleteSuccessFlagList = []
        while not done:
            for task in self.taskList:
                try:
                    self.logger.debug(
                        "Task Details =>" + str(task.info.key) + " , " + str(task.info.descriptionId) + " , " + str(
                            task.info.entityName))
                    if task.info.state == vim.TaskInfo.State.running:
                        self.logger.debug("'" + str(task.info.key) + "' progress = " + str(task.info.progress) + " %")
                        self.logger.debug("'" + str(task.info.key) + "' is running.")
                        taskDoneFlagList.append(0)
                    else:
                        self.logger.debug("'" + str(task.info.key) + "' is done.")
                        taskDoneFlagList.append(1)
                except:
                    # to catch self.logger.debug("Unexpected error:", sys.exc_info()[0])
                    self.logger.error("Unexpected error:", sys.exc_info()[0])
                    self.logger.error("PASS1")
                    pass

            # self.logger.debug("taskDoneFlagList value = " + str(taskDoneFlagList))
            # self.logger.debug(all(taskDoneFlagList))
            if all(taskDoneFlagList):
                # If all tasks complete this will be executed
                done = 1

            if not done:
                self.logger.debug("Waiting for " + str(self.sleeptime) + " seconds")
                time.sleep(int(self.sleeptime))

            taskDoneFlagList = []

        for task in self.taskList:
            try:
                if task.info.state == vim.TaskInfo.State.success:
                    self.logger.debug("Task Result =>" + str(task.info.result))
                    self.logger.debug("'" + str(task.info.key) + "' completed successfully")
                    taskCompleteSuccessFlagList.append(1)
                else:
                    self.logger.debug("Task Result " + str(task.info.result))
                    self.logger.debug("Task '" + str(task) + "' did not complete successfully")
                    taskCompleteSuccessFlagList.append(0)
            except:
                # to catch self.logger.debug("Unexpected error:", sys.exc_info()[0])
                self.logger.error("Unexpected error:", sys.exc_info()[0])
                self.logger.error("PASS2")
                taskCompleteSuccessFlagList.append(1)
                pass

        if all(taskCompleteSuccessFlagList):
            self.logger.debug(self.actionName + " operation completed sucessfully")
        else:
            self.logger.debug(
                self.actionName + " operation failed. Check vcenter for more info. Terminating execution now")
            exit()

    def create_vm(self, si, vmname, templatename, cpu, memory, ipaddr, mask, gateway, dnsip, ipflag, datastorename, domainname,
                  resourcepoolname):
        """
        method to create vm
        """
        self.si, self.vmname, self.templatename, self.cpu, self.memory, self.ipaddr, self.mask, self.gateway, self.dnsip ,self.ipflag, self.datastorename, \
        self.domainname, self.resourcepoolname = si, vmname, templatename, cpu, memory, ipaddr, mask, gateway, dnsip,ipflag, datastorename, domainname, resourcepoolname
        self.logger.info("Creating VM on datastore => " + self.datastorename)
        template_vm = self.get_vm_by_name(self.si, self.templatename)
        vmconf = vim.vm.ConfigSpec(numCPUs=self.cpu, memoryMB=self.memory)
        adaptermap = vim.vm.customization.AdapterMapping()
        adaptermap.adapter = vim.vm.customization.IPSettings(ip=vim.vm.customization.DhcpIpGenerator(),
                                                             dnsDomain=self.domainname)
        if self.ipflag.lower() == 'static':
            #print self.ipaddr, self.mask, self.gateway, self.dnsip
            self.logger.info("IP to be set in for VM '" + self.vmname + "' in template is '" + ipaddr + "'")
            adaptermap.adapter = vim.vm.customization.IPSettings(ip=vim.vm.customization.FixedIp(ipAddress=self.ipaddr),
                                                                 subnetMask=self.mask, gateway=self.gateway)
            #or mutiple adapters enhance this part
            # adaptermap.adapter = vim.vm.customization.IPSettings(ip=vim.vm.customization.FixedIp(address=ipaddr),
            #                                                     subnetMask=mask, gateway=gateway)
            globalip = vim.vm.customization.GlobalIPSettings(dnsServerList=self.dnsip)
        else:
            globalip = vim.vm.customization.GlobalIPSettings()

        #vmhostname = "-".join(self.vmname.split("-")[:2])
        vmhostname = self.vmname
        self.logger.info(
            "Deploying VM '" + self.vmname + "' on resourcepool '" + self.resourcepoolname + "' with hostname set as '" + vmhostname + "'")
        ident = vim.vm.customization.LinuxPrep(domain=self.domainname,
                                               hostName=vim.vm.customization.FixedName(name=vmhostname))
        customspec = vim.vm.customization.Specification(nicSettingMap=[adaptermap], globalIPSettings=globalip,
                                                        identity=ident)
        resource_pool = self.get_resource_pool(self.si, self.resourcepoolname)
        # hs = vmutils.get_host_by_name(si, "172.26.236.66")
        ds = self.get_datastore_by_name(self.si, self.datastorename)
        relocateSpec = vim.vm.RelocateSpec(pool=resource_pool, datastore=ds)
        # cloneSpec = vim.vm.CloneSpec(powerOn=True, template=False, location=relocateSpec,customization=customspec,config=vmconf)
        cloneSpec = vim.vm.CloneSpec(powerOn=False, template=False, location=relocateSpec, customization=customspec,
                                     config=vmconf)
        self.logger.info("VM '" + self.vmname + "' deployment triggered from template '" + self.templatename + "'")
        task = template_vm.Clone(name=self.vmname, folder=template_vm.parent, spec=cloneSpec)
        return task

    def change_vm_adapter_portgroup(self, si, vmname, pgname):
        change_adapter_task_list = []
        power_on_task_list = []
        self.si, self.vmname, self.pgname = si, vmname, pgname
        vm = self.get_vm_by_name(self.si, self.vmname)
        # This code is for changing only one Interface. For multiple Interface
        # Iterate through a loop of network names.
        device_change = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nicspec = vim.vm.device.VirtualDeviceSpec()
                nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                nicspec.device = device
                nicspec.device.wakeOnLanEnabled = True
                network = self._get_obj(self.si.RetrieveContent(), [vim.dvs.DistributedVirtualPortgroup], self.pgname)
                dvs_port_connection = vim.dvs.PortConnection()
                dvs_port_connection.portgroupKey = network.key
                dvs_port_connection.switchUuid = network.config.distributedVirtualSwitch.uuid
                nicspec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nicspec.device.backing.port = dvs_port_connection
                nicspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
                nicspec.device.connectable.startConnected = True
                nicspec.device.connectable.allowGuestControl = True
                device_change.append(nicspec)
                break
        config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
        self.logger.debug("Connecting VM '" + self.vmname + "' to network '" + self.pgname + "'")
        return vm.ReconfigVM_Task(config_spec)

    def vm_power_on(self, si, vmname):
        self.si, self.vmname = si, vmname
        vm = self.get_vm_by_name(self.si, self.vmname)
        self.logger.debug("Powering on VM '" + self.vmname + " ...'")
        return vm.PowerOn()

    def vm_power_off(self, si, vmname ):
        self.si, self.vmname  = si, vmname
        vm = self.get_vm_by_name(self.si, self.vmname)
        self.logger.debug("Powering off VM '" + self.vmname + "'")
        return vm.PowerOff()

    def vm_destroy(self, si, vmname):
        self.si, self.vmname,  = si, vmname
        vm = self.get_vm_by_name(self.si, self.vmname)
        self.logger.debug("Destroying VM '" + self.vmname + "'")
        return vm.Destroy()

    def vm_reboot(self, si, vmname ):
        self.si, self.vmname  = si, vmname
        vm = self.get_vm_by_name(self.si, self.vmname)
        self.logger.debug("Rebooting VM '" + self.vmname + "'")
        reboot_guest = False
        while not reboot_guest:
            try:
                self.logger.info("VM Tools state = " + str(vm.guest.toolsStatus))
                return vm.RebootGuest()
            except:
                self.logger.error(sys.exc_info())
                self.logger.info("System is not up. Waiting for 5 seconds before polling again")
                time.sleep(5)

    def vm_create_snapshot(self, si, vmname, snapshotname, description="Created by Automaton", memory=False,
                           quiesce=False):
        self.si, self.vmname = si, vmname
        vm = self.get_vm_by_name(self.si, self.vmname)
        self.snapshotname = snapshotname
        self.description = description
        self.memory = memory
        self.quiesce = quiesce
        self.logger.debug("Creating snapshot '%s' on  VM '%s'" % (self.snapshotname, self.vmname))
        return vm.CreateSnapshot(self.snapshotname, self.description, self.memory, self.quiesce)

    def get_vm_ipaddr(self, si, vmname):
        self.si, self.vmname = si, vmname
        vm = self.get_vm_by_name(self.si, self.vmname)
        return vm.summary.guest.ipAddress

    def vcenter_connect(self):
        try:
            self.logger.info("Connecting to Vcenter = " + self.vcip)
            si = SmartConnectNoSSL(host=self.vcip, user=self.user, pwd=self.password, port=self.vcenter_port)
            return si
        except IOError, e:
            sys.exit("Unable to connect to vsphere server. Error message: %s" % e)

    def vcenter_disconnect(self,si):
        # add a clean up routine
        self.logger.info("Disconnecting from vcenter")
        Disconnect(si)

    def vmware_create_vm(self,vcenter_si,vm_name_list, vm_template_name, ip_data_list, subnet_mask_list, gateway_list, dnsip_list, ip_type, datastore_name, domain_name,
                         resource_pool_name, port_group_list,vcpu,ramgb):
        #si = self.vcenter_connect()
        taskList = []
        adapter_change_task_list = []
        self.vcenter_si,self.vm_name_list,self.vm_template_name,self.ip_data_list, self.subnet_mask_list, self.gateway_list, self.dnsip_list, self.ip_type,self.datastore_name,\
        self.domain_name,self.resource_pool_name,self.port_group_list,self.vcpu,self.ramgb = vcenter_si,vm_name_list, vm_template_name, ip_data_list, subnet_mask_list, \
                                                                                        gateway_list, dnsip_list, ip_type,datastore_name, domain_name,resource_pool_name,\
                                                                                        port_group_list,vcpu,ramgb
        #print self.vm_name_list
        #print self.ip_data_list
        #print self.subnet_mask_list
        #print self.gateway_list
        #print self.dnsip_list

        for i in range(len(self.vm_name_list)):
            self.logger.info("Deploying VM '" + self.vm_name_list[i] + "' from vm template '" + self.vm_template_name + "'")
            taskList.append(self.create_vm(self.vcenter_si, vm_name_list[i], vm_template_name, self.vcpu,self.ramgb, self.ip_data_list[i], self.subnet_mask_list[i],
                                           self.gateway_list[i], self.dnsip_list[i],self.ip_type,
                                     self.datastore_name, self.domain_name, self.resource_pool_name))
        self.WaitTask(taskList,'VM clone task')
        for i in range(len(self.vm_name_list)):
            adapter_change_task_list.append(self.change_vm_adapter_portgroup(self.vcenter_si, self.vm_name_list[i], self.port_group_list[i]))
        self.WaitTask(adapter_change_task_list, 'Change PortGroup', sleeptime=10)
        vm_power_on_task_list = [self.vm_power_on(self.vcenter_si, vm) for vm in self.vm_name_list]
        self.WaitTask(vm_power_on_task_list, "Power On VM", sleeptime=10)
        #self.vcenter_disconnect(si)