#!/bin/bash
WAN=eth1

ip6tables-restore /etc/iptables/rules.v6

appliquer_regle() {
  HOSTNAME=$1
  PORT=$2

  IP=`getent hosts $HOSTNAME`
  if [ $? == 0 ]; then
    IP=`echo $IP | awk '{print $1}'`
    ip6tables -A INPUT --in-interface $WAN --protocol tcp --dport $PORT --destination $IP -j ACCEPT
    ip6tables -A FORWARD --in-interface $WAN --protocol tcp --dport $PORT --destination $IP -j ACCEPT
  else
    echo "Hostname $HOSTNAME inconnu, regle non applicable"
  fi
}

# Infraserv1
# REDMINE_IP=`gentent hosts redmine.maceroc.com`
appliquer_regle redmine.maceroc.com 443
appliquer_regle repository.maceroc.com 22
