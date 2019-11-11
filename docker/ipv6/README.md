# Docker avec IPv6

[English version](README_en.md)

## Pourquoi?

- La liste d'addresses IPv4 non attribuées est épuisée : https://en.wikipedia.org/wiki/IPv4_address_exhaustion.
  On est en mode de recyclage et de [recouvrement](https://www.iana.org/assignments/ipv4-recovered-address-space/ipv4-recovered-address-space.xhtml)!
- Internet of Things (IoT), j'en veux!
- NAT (Network Address Translation) goûte mauvais. Je m'étais fait dire que c'était
  bon pour ma sécurité, mais j'y crois autant qu'aux produits naturels.


# Recette

## Configurer ip forwarding

  Cette étape est nécessaire pour créer des sous-réseaux (par exemple avec Docker) mais
  on ne la testera pas immédiatement.

  **Instructions**
  1. Ouvrir une session sur l'ordinateur qui recevra le nouveau réseau.
  2. `sudo cp /etc/sysctl.conf /etc/sysctl.conf.old`
  3. Configurer le fichier /etc/sysctl.conf:
     - `sudo nano /etc/sysctl.conf`
     - Noter que eth0 est mon interface LAN - ajuster les instructions suivantes au besoin
     - Ajouter :
        ```
        net.ipv6.conf.all.forwarding=1
        ```
  4. `sudo sysctl -p`

  _Résultat affiché_

  ```
  [...]
  net.ipv6.conf.all.forwarding = 1
  [...]
  ```
