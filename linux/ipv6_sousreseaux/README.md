# Sous-réseaux avec IPv6 statique

[English version](README_en.md)

## Pourquoi?

- J'ai plusieurs systèmes virtuels (qemu) et j'utilise aussi docker. Je veux
  pouvoir accéder à ces ressources sans NAT ni _ndp proxy_.
- Le fournisseur internet avec lequel je fais affaire (TekSavvy via Rogers) ne
  donne pas accès à des adresses IPv6 **statiques** ni à des sous-réseaux (subnets)
  avec Prefix Delegation (PD) de /48 ou /56 bits.

## Nomenclature

- Un routeur très flexible déjà relié à internet. Dans mon cas j'utilise un RaspberryPi 2 que j'ai
  configuré avec ce projet: [Un RaspberryPi comme passerelle réseau](../rpi_passerelle/README.md)
  - Je dis très flexible parce que le routeur doit supporter les tables de routage
    multiples par IP source (ip rules) et une configuration poussée du filtre iptables.
- Un compte gratuit avec [Tunnelbroker](https://tunnelbroker.net/) de Hurricane Electric.
- Un ordinateur ou machine virtuelle avec Linux déjà fonctionnel avec IPv4 relié au
  réseau du routeur. J'utilise une machine virtuelle avec Ubuntu 18 Server.

## Avertissements

- Cette recette ne montre pas comment créer un tunnel avec TunnelBroker.
- Cette approche n'est probablement pas recommendable dans un environnement
  d'affaires, c'est plus approprié pour un individu qui désire explorer IPv6.

## Préparation

Créer un tunnel /48 sur [Tunnelbroker](https://tunnelbroker.net/) - c'est gratuit.
il suffit de s'enregistrer, créer un tunnel (/64) puis de cliquer sur le
bouton _Assign /48_. Ces adresses sont statiques - j'en ai une depuis plus de
3 ans et elle n'a jamais changée.

En ce moment, Tunnelbroker permet de créer 5 tunnels gratuits.

## Recette

1. `ip tunnel add he-ipv6 mode sit remote 216.66.38.58 local 24.246.8.56 ttl 255`
2. `ip link set he-ipv6 up`
3. `ip addr add 2001:470:1c:11d::2/64 dev he-ipv6`

# Références

- TunnelBroker de Hurricane Electric : https://tunnelbroker.net
- https://unix.stackexchange.com/questions/22770/two-interfaces-two-addresses-two-gateways
