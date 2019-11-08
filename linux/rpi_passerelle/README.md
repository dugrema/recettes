# Un RaspberryPi comme passerelle réseau

[English version](README_en.md)

## Pourquoi?

- Je veux davantage de contrôle sur IPv6. Mon fournisseur Internet (TekSavvy via Rogers)
  donne uniquement des préfixes /64; ceci m'empêche de créer des sous-réseaux avec délégation
  de préfixes de la manière prévue par IPv6.
- Je n'ai pas trouvé de routeurs domestiques abordables qui me permettent de
  contrôler la table de routage IPv6 après redémarrage.

## Nomenclature

- Un RaspberryPi de n'importe quel modèle en kit (avec carte _Secure Digital_,
  source d'alimentation électrique)
- Selon le modèle de RaspberryPi, un ou deux connecteurs Ethernet via USB
- Une connexion à internet avec un modem sans routeur ou un
  modem/routeur qui peut être contourné - tous avec connecteurs Ethernet
- Routeur en mode _bridge_ ou une _switch_ réseau
- Idéalement un écran et clavier pour le RaspberryPi

## Préparation

Le RaspberryPi doit être déjà initialisé. J'ai utilisé le système d'exploitation
Raspbian (https://www.raspberrypi.org/downloads/).

```
1. sudo apt update
2. sudo apt -y upgrade
```

### Avertissements

- J'utilise régulièrement Ubuntu sur les RaspberryPi. J'ai tenté d'utiliser la Version
  19.10 armhf sur un RPi2 pour ce projet; je ne suis pas arrivé à faire fonctionner
  le _IP Forwarding_ des connexions TCP même si ICMP (ping, traceroute) fonctionnait bien.
- Une mauvaise configuration du pare feu peut rendre votre réseau interne
  accessible d'internet (situation généralement indésirable).

## Recette

### Préparer les connexions réseau

J'utilise Raspbian buster lite. Cette distribution utilise ifupdown pour la
configuration réseau.

```
1. sudo cp /etc/network/interfaces /etc/network/interfaces.old
2. Copier le fichier [interfaces](interfaces) vers /etc/network
3. Modifier le nom des interfaces au besoin. Dans mon cas, eth0 = LAN et eth1 = WAN.
4. sudo /etc/init.d/networking restart
```

S'assurer que les interfaces réseau sont bien configurées sur IPv4:

`ip a`

> 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
>    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
>    inet 127.0.0.1/8 scope host lo
>       valid_lft forever preferred_lft forever
>    inet6 ::1/128 scope host
>       valid_lft forever preferred_lft forever
>2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
>    link/ether b8:27:eb:01:d0:fe brd ff:ff:ff:ff:ff:ff
>    **inet 192.168.1.1/24 brd 192.168.1.255 scope global eth0**
>       valid_lft forever preferred_lft forever
>    inet6 fe80::ba27:ebff:fe01:d0fe/64 scope link
>       valid_lft forever preferred_lft forever
>3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
>    link/ether 00:24:49:02:b4:c2 brd ff:ff:ff:ff:ff:ff
>    **inet 24.246.11.89/27 brd 255.255.255.255 scope global dynamic eth1**
>       valid_lft 167789sec preferred_lft 167789sec
>    inet6 fe80::224:49ff:fe02:b4c2/64 scope link
>       valid_lft forever preferred_lft forever

### Installer wide-dhcpv6-client

_wide-dhcpv6-client_ est le premier client DHCP avec lequel j'ai réussi à faire
fonctionner IPv6-PD (Prefix Delegation). C'est probablement possible de le faire
avec le client dhcp intégré à Raspbian, je n'ai juste pas trouvé la recette.

```
1. sudo apt install -y wide-dhcpv6-client
2. sudo cp /etc/wide-dhcpv6/dhcp6c.conf /etc/wide-dhcpv6/dhcp6c.conf.old
2. sudo nano /etc/wide-dhcpv6/dhcp6c.conf
   a. Remplacer le contenu par ce fichier : [dhcp6c.conf](dhcp6c.conf)
   b. Dans ma version, eth1 représente le réseau externe (WAN via USB) et eth0 le réseau
      interne (connexion réseau intégrée au RPi). Vous pouvez ajuster selon votre
      configuration.
3. sudo systemctl restart wide-dhcpv6-client
```

Goûter avant de poursuivre:

_Confirmer que le client fonctionne_

`sudo tail -100 /var/log/syslog`

>Nov  8 02:17:38 pi-host1 wide-dhcpv6-client[1071]: Starting WIDE DHCPv6 client: dhcp6c.
>Nov  8 02:17:38 pi-host1 systemd[1]: Started LSB: Start/Stop WIDE DHCPv6 client.
>Nov  8 02:17:48 pi-host1 dnsmasq-dhcp[578]: RTR-ADVERT(eth0) 2607:f2c0:eb70:3c::

_Vérifier que les adresses IPv6 globales ont été attribuées_

`ip -6 a`

>1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
>    inet6 ::1/128 scope host
>       valid_lft forever preferred_lft forever
>2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
>    **inet6 2607:f2c0:eb70:12ca::1/64 scope global**
>       valid_lft forever preferred_lft forever
>    inet6 fe80::ba27:ebff:fe01:d0fe/64 scope link
>       valid_lft forever preferred_lft forever
>3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
>    **inet6 2607:f2c0:f200:1903:f465:b17b:7ba8:6905/128 scope global**
>       valid_lft forever preferred_lft forever
>    inet6 fe80::224:49ff:fe02:b4c2/64 scope link
>       valid_lft forever preferred_lft forever

### Installer dnsmasq

```
1. sudo apt install dnsmasq
2. sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.old
3. sudo nano /etc/dnsmasq.conf

```

### Configurer ip forwarding

```
1. sudo cp /etc/sysctl.conf /etc/sysctl.conf.old
2. sudo nano /etc/sysctl.conf
   a. ajouter les lignes suivantes :
   b. net.ipv4.ip_forward=1
   c. net.ipv6.conf.all.forwarding=1
   d. net.ipv6.conf.eth1.accept_ra=2
3. sudo sysctl -p
```

### Configurer le pare feu

```
1. apt install -y iptables-persistent
2. sudo cp /etc/iptables/rules.v4 /etc/iptables/rules.v4.old
3. sudo cp /etc/iptables/rules.v6 /etc/iptables/rules.v6.old
4. Copier les fichiers [rules.v4](rules.v4) et [rules.v6](rules.v6) vers /etc/iptables
5. Au besoin, ajuster les interfaces dans rules.v4 et rules.v6:
   a. Dans mon cas: eth0 = LAN, eth1 = WAN
6. iptables-restore /etc/iptables/rules.v4
7. ip6tables-restore /etc/iptables/rules.v6
```

# Le goûteur

1. S'assurer de pouvoir exécuter des requêtes ICMP (ping, traceroute) vers internet à partir du RasberryPi.
2. Si tout fonctionne, essayer la même procédure à partir d'une machine connectée du LAN.
3. Vérifier la connectivité _DNS_ avec dnsmasq à partir d'une machine sur le LAN en faisant une requête dig (e.g. dig www.google.ca \@192.168.1.1)
4. Vérifier la connectivité _TCP_ en faisant une requête web (http://www.google.ca dans un navigateur)

# Références

- **Référence délicieuse** Using dnsmasq on a Linux router for DHCPv6 : https://hveem.no/using-dnsmasq-for-dhcpv6
- Dnsmasq : http://www.thekelleys.org.uk/dnsmasq/doc.html
- Systèmes d'exploitation pour RaspberryPi : https://www.raspberrypi.org/downloads/

## Reférences additionnelles

- https://medium.com/@niktrix/getting-rid-of-systemd-resolved-consuming-port-53-605f0234f32f
- https://unix.stackexchange.com/questions/437907/dnsmasq-always-returning-refused
- https://www.cyberciti.biz/faq/unix-linux-check-if-port-is-in-use-command/
- https://www.cyberciti.biz/faq/howto-set-sysctl-variables/
- https://raspberrypi.stackexchange.com/questions/39227/rpi-as-internet-gateway-bridge?rq=1
- https://resources.sei.cmu.edu/tools/downloads/vulnerability-analysis/assets/IPv6/ip6tables_rules.txt
- https://forum.openwrt.org/t/configuring-dns-using-dnsmasq-dhcp-and-dynamic-ipv6-firewall-rules/43392