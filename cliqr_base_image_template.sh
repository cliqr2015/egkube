#!/bin/bash

OS_TYPE=`python -mplatform | grep -q Ubuntu && echo "Ubuntu" || echo "CentOS"`
CENTOS_RELEASE_VER=`python -mplatform | awk -F '-' '{ print $(NF-1) }' | awk -F '.' '{ print $1 }'`
UBUNTU_RELEASE_VER=`python -mplatform | awk -F '-' '{ print $(NF-1) }'`
UBUNTU_RELEASE_NAME=`python -mplatform | awk -F '-' '{ print $(NF) }'`

if [ "$OS_TYPE" = "CentOS" ]; then
	echo "Centos $CENTOS_RELEASE_VER"

	case $CENTOS_RELEASE_VER in
		'7')
			rpm -Uhv http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm
			;;
		'6')
			rpm -Uhv http://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
			;;
		'*')
			echo "$CENTOS_RELEASE_VER is not supported"
			;;
	esac
fi

yum -y install oprofile.x86_64 perf.x86_64 iotop dropwatch.x86_64 htop.x86_64 atop.x86_64 iftop.x86_64 iperf3.x86_64 tuned.noarch net-tools ntp wget bind-utils perl

# Configure tuned for virtual guest
tuned-adm profile virtual-guest
systemctl enable tuned

# Disable unwanted services
for i in cups abrtd abrt-ccpp atd kdump mdmonitor ; do systemctl disable $i; done
for i in cups abrtd abrt-ccpp atd kdump mdmonitor ; do systemctl stop $i; done


# Disable SELinux
sed -i "s:enforcing:disabled:g" /etc/sysconfig/selinux
sed -i "s:enforcing:disabled:g" /etc/selinux/config


# Configure UTC timezone
echo "TZif2UTCTZif2UTC
UTC0" > /etc/localtime

echo "ZONE="UTC"
UTC=true
ARC=false" > /etc/sysconfig/clock

systemctl enable ntpd
systemctl enable ntpdate

systemctl start ntpdate
systemctl start ntpd

# Rename network interfaces to ETH instead of EN
sed -i "/^GRUB_CMDLINE_LINUX/ s/\"$/ net.ifnames=0 biosdevname=0\"/" /etc/default/grub
grub2-mkconfig -o /boot/grub2/grub.cfg

NIC=`ifconfig| grep flags | grep en | awk -F":" '{ print $1 }'`
cd /etc/sysconfig/network-scripts
mv ifcfg-"$NIC" ifcfg-eth0
sed -i "s:NAME=$NIC:NAME=eth0:g" ifcfg-eth0


# Disable IPv6
echo "NETWORKING_IPV6=no
IPV6INIT=no
NOZEROCONF=yes" >> /etc/sysconfig/network

echo "
# Disable IPv6
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
" >> /etc/sysctl.conf

sysctl -p

reboot
