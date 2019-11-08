#!/bin/bash
DEV=eth0

extraire_ip6_ipcommand_device() {
  DEV=$1
  NET=`ip -6 a show dev $DEV | grep -e inet6 | grep -e "scope global" | awk '{print $2}'`
  IP=`echo "$NET" | awk 'BEGIN {FS="/"}{print $1}'`
#  echo $IP
}

extraire_subnet64() {
  NET=$1
  SUBNET=`echo $NET | awk 'BEGIN {FS=":"} {print $1":"$2":"$3":"$4}'`
}

extraire_ip6_ipcommand_device $DEV
extraire_subnet64 $IP

# Ajouter les routes predefinies
ip route add $SUBNET:102::1/80 via fe80::5054:ff:fe92:9b05 dev $DEV

