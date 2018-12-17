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

### What does it do 
Creates a Kubernets Cluster which is ready for dev/test. 
1. Has support for dynamic volume provisioning using Helm
2. Capable of addons as provided in the 'task' section
3. Supports kuberntes nodes with static/dynamic IP addressing

### Prerequistes
1. Currently works on Vmware 
2. Needs a Vmware VM template to start off
3. Existing NFS Server
4. Vmware distributed vSwitch

### Input
The input json needs details specific to vmware and the ova to be used.

### Sample OVA 
`
http://172.26.236.48/OVA/KubernetesBase/
`
