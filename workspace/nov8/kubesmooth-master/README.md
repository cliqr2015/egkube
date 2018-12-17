#Smooth and simple kuberntes deployment installation
```
           \
            \          __---__
                    _-       /--______
               __--( /     \ )XXXXXXXXXXX\v.
             .-XXX(   O   O  )XXXXXXXXXXXXXXX-
            /XXX(       U     )        XXXXXXX\
          /XXXXX(              )--_  XXXXXXXXXXX\
         /XXXXX/ (      O     )   XXXXXX   \XXXXX\
         XXXXX/   /            XXXXXX   \__ \XXXXX
         XXXXXX__/          XXXXXX         \__---->
 ---___  XXX__/          XXXXXX      \__         /
   \-  --__/   ___/\  XXXXXX            /  ___--/=
    \-\    ___/    XXXXXX              '--- XXXXXX
       \-\/XXX\ XXXXXX                      /XXXXX
         \XXXXXXXXX   \                    /XXXXX/
          \XXXXXX      >                 _/XXXXX/
            \XXXXX--__/              __-- XXXX/
             -XXXXXXXX---------------  XXXXXX-
                \XXXXXXXXXXXXXXXXXXXXXXXXXX/
                  ""VXXXXXXXXXXXXXXXXXXV""


```


### How to use ?

`
python deploy.py -i <input-file.json>
`

### What does it do 
Creates a Kubernets Cluster which is ready for dev/test. 
1. Has support for dynamic volume provisioning using Helm
2. Capable of addons as provided in the 'task' section
3. Supports kubernetes nodes with static/dynamic IP addressing
3. Creates admin and cisco user with separate kubeconfig. Cisco is needed for multicloud suite

### Prerequistes
1. Currently works on Vmware 
2. Needs a Vmware VM template to start off 
3. Existing NFS Server/ New NFS Servers
4. Vmware distributed vSwitch
5. Specified Pod Network

### Input
The input json needs details specific to vmware and the ova to be used.
1. Vcenter credentials
2. Vmname prefix
3. Static ip list / Dynamic
4. ip details(subnet,mask,gateway,dns,domain)
5. VM network info
6. NFS Server details (existing /if new required)
7. NFS subnet

### Tasks
1. Tasks can be added to trigger script execution on master node after the provisioning completes
   Example : Start Multicloud Suite installation after the cluster is setup !!


`
helm install --name c3-framework --set global.namespace=cisco,global.suiteMonitoring=false,global.suiteLogging=false <helm chart url>
`
### Sample OVA 
`
http://172.26.236.48/OVA/K8-Base/
`
