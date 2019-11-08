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
Raspbian buster lite (https://www.raspberrypi.org/downloads/).

Ici j'assume un travail directement sur le RaspberryPi. Pour travailler à
distance, il faudra préparer une adresse IPv4 statique ou mieux encore,
installer avahi-daemon, donner un nom au RaspberryPi ce qui permettra
d'utiliser l'adresse IPv6 link-local (fe80::...). En autant que votre station
de travail supporte mDNS, bien sûr!

**Instructions**
```
1. sudo apt update
2. sudo apt -y upgrade
```

### Avertissements

- J'utilise régulièrement Ubuntu sur les RaspberryPi. J'ai tenté d'utiliser la version
  19.10 armhf sur un RPi2 pour ce projet; je ne suis pas arrivé à faire fonctionner
  le _IP Forwarding_ des connexions TCP même si ICMP (ping, traceroute) fonctionnait bien.
- Une mauvaise configuration du pare feu peut rendre votre réseau interne
  accessible d'internet. Pour ceux qui viennent juste de penser "et pis quoi?",
  j'ajouterais simplement que c'est une situation généralement indésirable à
  cause Russie et Corée du Nord.

## Recette

### Préparer les connexions réseau

J'utilise Raspbian buster lite. Cette distribution utilise ifupdown pour la
configuration réseau avec dhcpcd pour la configuration des adresses.

**Instructions**
```
1. sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.old
2. Copier le fichier [dhcpcd.conf](dhcpcd.conf) vers /etc/dhcpcd.conf
3. Modifier le nom des interfaces dans le fichier, au besoin.
   Dans mon cas, eth0 = LAN et eth1 = WAN.
4. sudo systemctl restart networking
5. sudo systemctl daemon-reload
6. sudo systemctl restart dhcpcd
```

_Vérifier que networking est redémarré correctement_
`systemctl status networking`

_Résultat_
```
● networking.service - Raise network interfaces
   Loaded: loaded (/lib/systemd/system/networking.service; enabled; vendor preset: enabled)
   Active: active (exited) since Fri 2019-11-08 17:44:44 GMT; 12s ago
     Docs: man:interfaces(5)
  Process: 798 ExecStart=/sbin/ifup -a --read-environment (code=exited, status=0/SUCCESS)
 Main PID: 798 (code=exited, status=0/SUCCESS)

Nov 08 17:44:43 pi-host1 systemd[1]: Starting Raise network interfaces...
Nov 08 17:44:44 pi-host1 systemd[1]: Started Raise network interfaces.
```

`systemctl status dhcpcd`

_Résultat_
```
● dhcpcd.service - dhcpcd on all interfaces
   Loaded: loaded (/lib/systemd/system/dhcpcd.service; enabled; vendor preset: enabled)
  Drop-In: /etc/systemd/system/dhcpcd.service.d
           └─wait.conf
   Active: active (running) since Fri 2019-11-08 18:07:08 GMT; 4min 35s ago
  Process: 920 ExecStart=/usr/lib/dhcpcd5/dhcpcd -q -w (code=exited, status=0/SUCCESS)
 Main PID: 934 (dhcpcd)
    Tasks: 1 (limit: 2319)
   Memory: 1.2M
   CGroup: /system.slice/dhcpcd.service
           └─934 /sbin/dhcpcd -q -w
```

_S'assurer que les interfaces réseau sont bien configurées sur IPv4 :_

`ip -4 a`

_Résultat_
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    inet 192.168.1.1/24 brd 192.168.1.255 scope global eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    inet 24.246.11.89/27 brd 255.255.255.255 scope global dynamic eth1
       valid_lft 165919sec preferred_lft 165919sec
```

### Installer wide-dhcpv6-client

_wide-dhcpv6-client_ est le premier client DHCP avec lequel j'ai réussi à faire
fonctionner IPv6-PD (Prefix Delegation). C'est probablement possible de le faire
avec le client dhcpcd intégré à Raspbian, je n'ai juste pas trouvé la recette.

**Instructions**
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

_Confirmer que le client fonctionne_

`sudo systemctl status wide-dhcpv6-client`

_Résultat_
```
● wide-dhcpv6-client.service - LSB: Start/Stop WIDE DHCPv6 client
   Loaded: loaded (/etc/init.d/wide-dhcpv6-client; generated)
   Active: active (running) since Fri 2019-11-08 15:14:03 GMT; 6s ago
     Docs: man:systemd-sysv-generator(8)
  Process: 2284 ExecStart=/etc/init.d/wide-dhcpv6-client start (code=exited, status=0/SUCCESS)
    Tasks: 1 (limit: 2319)
   Memory: 1.2M
   CGroup: /system.slice/wide-dhcpv6-client.service
           └─2289 /usr/sbin/dhcp6c -Pdefault eth1

Nov 08 15:14:01 pi-host1 systemd[1]: Starting LSB: Start/Stop WIDE DHCPv6 client...
Nov 08 15:14:03 pi-host1 wide-dhcpv6-client[2284]: Starting WIDE DHCPv6 client: dhcp6c.
Nov 08 15:14:03 pi-host1 systemd[1]: Started LSB: Start/Stop WIDE DHCPv6 client.
```

_Vérifier que les adresses IPv6 globales ont été attribuées_

`ip -6 a`

_Résultat_
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    **inet6 2607:f2c0:eb70:12ca::1/64 scope global**
       valid_lft forever preferred_lft forever
    inet6 fe80::ba27:ebff:fe01:d0fe/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    **inet6 2607:f2c0:f200:1903:f465:b17b:7ba8:6905/128 scope global**
       valid_lft forever preferred_lft forever
    inet6 fe80::224:49ff:fe02:b4c2/64 scope link
       valid_lft forever preferred_lft forever
```

### Installer dnsmasq

**Instructions**
```
1. sudo apt install dnsmasq
2. sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.old
3. Copier le fichier [dnsmasq.conf](dnsmasq.conf) vers /etc
4. Modifier le nom des interfaces dans le fichier, au besoin.
   Dans mon cas, eth0 = LAN et eth1 = WAN.
5. sudo systemctl restart dnsmasq
```

_Vérifier que dnsmasq est démarré correctement_

`systemctl status dnsmasq`

_Résultat_
```
● dnsmasq.service - dnsmasq - A lightweight DHCP and caching DNS server
   Loaded: loaded (/lib/systemd/system/dnsmasq.service; enabled; vendor preset: enabled)
   Active: active (running) since Fri 2019-11-08 17:52:41 GMT; 29min ago
 Main PID: 411 (dnsmasq)
    Tasks: 1 (limit: 2319)
   Memory: 2.8M
   CGroup: /system.slice/dnsmasq.service
           └─411 /usr/sbin/dnsmasq -x /run/dnsmasq/dnsmasq.pid -u dnsmasq -r /run/dnsma ...
```

### Configurer ip forwarding

**Instructions**
```
1. sudo cp /etc/sysctl.conf /etc/sysctl.conf.old
2. Ajouter les lignes suivantes au fichier /etc/sysctl.conf:
   a. sudo nano /etc/sysctl.conf
   b. Noter que eth1 est mon interface WAN - ajuster les instructions suivantes au besoin
   c. Ajouter :
      net.ipv4.ip_forward=1
      net.ipv6.conf.all.forwarding=1
      net.ipv6.conf.eth1.accept_ra=2
3. sudo sysctl -p
```

### Configurer le pare feu

**Instructions**
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
