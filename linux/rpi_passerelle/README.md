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
1. `sudo apt update`
2. `sudo apt -y upgrade`

### Avertissements

- J'utilise régulièrement Ubuntu sur les RaspberryPi. J'ai tenté d'utiliser la version
  19.10 armhf sur un RPi2 pour ce projet; je ne suis pas arrivé à faire fonctionner
  le _IP Forwarding_ des connexions TCP même si ICMP (ping, traceroute) fonctionnait bien.
- Une mauvaise configuration du pare feu peut rendre votre réseau interne
  accessible d'internet. Pour ceux qui viennent juste de penser "et pis quoi?",
  j'ajouterais simplement que c'est une situation généralement indésirable à
  cause Russie et Corée du Nord.

## Recette

### Configurer le pare feu

On configure le pare feu à cette étape pour s'assurer d'avoir une connexion
à internet relativement sécuritaire. La connexion internet est probablement
déjà prête à l'emploi si votre fournisseur internet fonctionne par DHCP.

**Fichiers**
- [rules.v4](rules.v4)
- [rules.v6](rules.v6)

**Instructions**
1. `apt install -y iptables-persistent`
2. A la question _save current IPv4 rules_ (et IPv6), repondre oui.
2. `sudo cp /etc/iptables/rules.v4 /etc/iptables/rules.v4.old`
3. `sudo cp /etc/iptables/rules.v6 /etc/iptables/rules.v6.old`
4. Copier les fichiers [rules.v4](rules.v4) et [rules.v6](rules.v6) vers /etc/iptables
5. Au besoin, ajuster les interfaces dans rules.v4 et rules.v6.
   Dans mon cas: eth0 = LAN, eth1 = WAN
6. `sudo iptables-restore /etc/iptables/rules.v4`
7. `sudo ip6tables-restore /etc/iptables/rules.v6`

_Vérifier que les règles sont bien chargées_

**Exécuter :** `sudo iptables -L -vn`

_Résultat_

```
Chain INPUT (policy DROP 3 packets, 120 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0
    1    76 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
  170 19334 ACCEPT     all  --  eth0   *       0.0.0.0/0            0.0.0.0/0            state NEW

Chain FORWARD (policy DROP 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     all  --  eth1   eth0    0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED
    0     0 ACCEPT     all  --  eth0   eth1    0.0.0.0/0            0.0.0.0/0
    0     0 REJECT     all  --  eth1   eth0    0.0.0.0/0            0.0.0.0/0            reject-with icmp-port-unreachable

Chain OUTPUT (policy ACCEPT 108 packets, 10299 bytes)
 pkts bytes target     prot opt in     out     source               destination
```

**Exécuter :** `sudo iptables -t nat -L -vn`

```
Chain PREROUTING (policy ACCEPT 292 packets, 21940 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain INPUT (policy ACCEPT 136 packets, 12593 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    1    76 MASQUERADE  all  --  *      eth1    0.0.0.0/0            0.0.0.0/0

Chain OUTPUT (policy ACCEPT 1 packets, 76 bytes)
 pkts bytes target     prot opt in     out     source               destination
```

**Exécuter :** `sudo ip6tables -L -vn`

```
Chain INPUT (policy DROP 2 packets, 148 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     all      lo     *       ::/0                 ::/0
   71  5312 ACCEPT     all      *      *       ::/0                 ::/0                 state RELATED,ESTABLISHED
   19  5892 ACCEPT     all      eth0   *       ::/0                 ::/0                 state NEW
    0     0 ACCEPT     udp      eth1   *       fe80::/16            ::/0                 udp dpt:546
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 1
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 2
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 3
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 4
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 128 limit: avg 15/sec burst 5
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 129 limit: avg 15/sec burst 5
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 134 HL match HL == 255
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 135 HL match HL == 255
    0     0 ACCEPT     icmpv6    *      *       ::/0                 ::/0                 ipv6-icmptype 136 HL match HL == 255

Chain FORWARD (policy DROP 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination
    0     0 ACCEPT     all      eth1   eth0    ::/0                 ::/0                 state RELATED,ESTABLISHED
    0     0 ACCEPT     all      eth0   eth1    ::/0                 ::/0
    0     0 ACCEPT     all      eth0   eth0    ::/0                 ::/0

Chain OUTPUT (policy ACCEPT 57 packets, 8720 bytes)
 pkts bytes target     prot opt in     out     source               destination
```

### Préparer les connexions réseau

J'utilise Raspbian buster lite. Cette distribution utilise ifupdown pour la
configuration réseau avec dhcpcd pour la configuration des adresses.

**Fichiers**
- [dhcpcd.conf](dhcpcd.conf)

**Instructions**
1. `sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.old`
2. Copier le fichier [dhcpcd.conf](dhcpcd.conf) vers /etc
3. Modifier le nom des interfaces dans le fichier, au besoin.
   Dans mon cas, eth0 = LAN et eth1 = WAN.
4. `sudo systemctl restart networking`
5. `sudo systemctl daemon-reload`
6. `sudo systemctl restart dhcpcd`

_Vérifier que networking est redémarré correctement_

**Exécuter :** `systemctl status networking`

_Résultat_
```
● networking.service - Raise network interfaces
   Loaded: loaded (/lib/systemd/system/networking.service; enabled; vendor preset: enabled)
   Active: active (exited) since Thu 2019-09-26 01:38:30 BST; 31s ago
     Docs: man:interfaces(5)
 Main PID: 597 (code=exited, status=0/SUCCESS)
    Tasks: 0 (limit: 2319)
   Memory: 0B
   CGroup: /system.slice/networking.service
```

**Exécuter :** `sudo systemctl status dhcpcd`

_Résultat_
```
● dhcpcd.service - dhcpcd on all interfaces
   Loaded: loaded (/lib/systemd/system/dhcpcd.service; enabled; vendor preset: enabled)
  Drop-In: /etc/systemd/system/dhcpcd.service.d
           └─wait.conf
   Active: active (running) since Thu 2019-09-26 01:45:24 BST; 1min 11s ago
  Process: 1059 ExecStart=/usr/lib/dhcpcd5/dhcpcd -q -w (code=exited, status=0/SUCCESS)
 Main PID: 1079 (dhcpcd)
    Tasks: 1 (limit: 2319)
   Memory: 1.3M
   CGroup: /system.slice/dhcpcd.service
           └─1079 /sbin/dhcpcd -q -w

Sep 26 01:45:24 ns1 systemd[1]: Started dhcpcd on all interfaces.
Sep 26 01:45:29 ns1 dhcpcd[1079]: eth1: using IPv4LL address 169.254.229.104
Sep 26 01:45:29 ns1 dhcpcd[1079]: eth1: adding route to 169.254.0.0/16
Sep 26 01:45:29 ns1 dhcpcd[1079]: eth1: adding default route
Sep 26 01:45:29 ns1 dhcpcd[1079]: eth1: leased 24.246.8.56 for 155325 seconds
Sep 26 01:45:29 ns1 dhcpcd[1079]: eth1: adding route to 24.246.8.32/27
Sep 26 01:45:29 ns1 dhcpcd[1079]: eth1: changing default route via 24.246.8.33
Sep 26 01:45:29 ns1 dhcpcd[1079]: eth1: deleting route to 169.254.0.0/16
Sep 26 01:45:31 ns1 dhcpcd[1079]: eth0: no IPv6 Routers available
Sep 26 01:45:31 ns1 dhcpcd[1079]: eth1: no IPv6 Routers available
```

_S'assurer que les interfaces réseau sont bien configurées sur IPv4 :_

**Exécuter :** `ip -4 a`

_Résultat_
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    inet 192.168.1.1/24 brd 192.168.1.255 scope global noprefixroute eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    inet 24.246.8.56/27 brd 255.255.255.255 scope global noprefixroute eth1
       valid_lft forever preferred_lft forever
```

### Installer wide-dhcpv6-client

_wide-dhcpv6-client_ est le premier client DHCP avec lequel j'ai réussi à faire
fonctionner IPv6-PD (Prefix Delegation). C'est probablement possible de le faire
avec le client dhcpcd intégré à Raspbian, je n'ai juste pas trouvé la recette.

**Fichiers**
- [dhcp6c.conf](dhcp6c.conf)

**Instructions**
1. `sudo apt install -y wide-dhcpv6-client`
   - À la question sur l'interface réseau
     (Interfaces on which the DHCPv6 client sends requests),
     répondre par votre interface WAN.
   - Dans mon cas c'est eth1.
2. `sudo cp /etc/wide-dhcpv6/dhcp6c.conf /etc/wide-dhcpv6/dhcp6c.conf.old`
3. Copier le fichier [dhcp6c.conf](dhcp6c.conf) vers /etc/wide-dhcpv6
   Note: Dans ma version, eth1 représente le réseau externe (WAN via USB) et
   eth0 le réseau interne (connexion réseau intégrée au RPi). Vous pouvez
   ajuster selon votre configuration.
4. `sudo systemctl restart wide-dhcpv6-client`

_Confirmer que le client fonctionne_

**Exécuter :** `sudo systemctl status wide-dhcpv6-client`

_Résultat_
```
● wide-dhcpv6-client.service - LSB: Start/Stop WIDE DHCPv6 client
   Loaded: loaded (/etc/init.d/wide-dhcpv6-client; generated)
   Active: active (running) since Fri 2019-11-08 21:51:38 GMT; 7s ago
     Docs: man:systemd-sysv-generator(8)
  Process: 2036 ExecStart=/etc/init.d/wide-dhcpv6-client start (code=exited, status=0/SUCCESS)
    Tasks: 1 (limit: 2319)
   Memory: 872.0K
   CGroup: /system.slice/wide-dhcpv6-client.service
           └─2040 /usr/sbin/dhcp6c -Pdefault eth1

Nov 08 21:51:36 ns1 systemd[1]: Starting LSB: Start/Stop WIDE DHCPv6 client...
Nov 08 21:51:38 ns1 wide-dhcpv6-client[2036]: Starting WIDE DHCPv6 client: dhcp6c.
Nov 08 21:51:38 ns1 systemd[1]: Started LSB: Start/Stop WIDE DHCPv6 client.
```

_Vérifier que les adresses IPv6 globales ont été attribuées_

**Exécuter :** `ip -6 a`

_Résultat_
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 2607:f2c0:eb70:1242::1/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::9ec4:862e:d432:37c3/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP qlen 1000
    inet6 2607:f2c0:f200:1903:69c3:89ee:d0ac:6fd1/128 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::7faa:eb34:19a9:7383/64 scope link
       valid_lft forever preferred_lft forever
```

### Installer dnsmasq

**Fichiers**
- [dnsmasq.conf](dnsmasq.conf)

**Instructions**
1. `sudo apt install dnsmasq`
2. `sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.old`
3. Copier le fichier [dnsmasq.conf](dnsmasq.conf) vers /etc
4. Modifier le nom des interfaces dans le fichier, au besoin.
   Dans mon cas, eth0 = LAN et eth1 = WAN.
5. `sudo systemctl restart dnsmasq`

_Vérifier que dnsmasq est démarré correctement_

**Exécuter :** `systemctl status dnsmasq`

_Résultat_
```
● dnsmasq.service - dnsmasq - A lightweight DHCP and caching DNS server
   Loaded: loaded (/lib/systemd/system/dnsmasq.service; enabled; vendor preset: enabled)
   Active: active (running) since Fri 2019-11-08 21:54:00 GMT; 7s ago
  Process: 2392 ExecStartPre=/usr/sbin/dnsmasq --test (code=exited, status=0/SUCCESS)
  Process: 2393 ExecStart=/etc/init.d/dnsmasq systemd-exec (code=exited, status=0/SUCCESS)
  Process: 2401 ExecStartPost=/etc/init.d/dnsmasq systemd-start-resolvconf (code=exited, status=0/SUCCESS)
 Main PID: 2400 (dnsmasq)
    Tasks: 1 (limit: 2319)
   Memory: 1.2M
   CGroup: /system.slice/dnsmasq.service
           └─2400 /usr/sbin/dnsmasq -x /run/dnsmasq/dnsmasq.pid -u dnsmasq -r /run/dnsmasq/resolv.conf -7 ...
```

### Configurer ip forwarding

**Instructions**
1. `sudo cp /etc/sysctl.conf /etc/sysctl.conf.old`
2. Configurer le fichier /etc/sysctl.conf:
   - `sudo nano /etc/sysctl.conf`
   - Noter que eth1 est mon interface WAN - ajuster les instructions suivantes au besoin
   - Ajouter :
      ```
      net.ipv4.ip_forward=1
      net.ipv6.conf.all.forwarding=1
      net.ipv6.conf.eth1.accept_ra=2
      ```
3. `sudo sysctl -p`

_Résultat affiché_

```
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.ipv6.conf.eth1.accept_ra = 2
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
