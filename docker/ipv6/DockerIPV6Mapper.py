#!/usr/bin/python3

import logging
import json
import hashlib
import binascii
import argparse
import sys
import os

import docker


class DockerIPV6Mapper:
    """
    Mappeur d'adresse IPv6 pour les containers docker.
    """

    def __init__(self):
        self.__docker = docker.from_env()
        self.args = None
        self.__logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def events(self):
        for raw_data in self.__docker.events():
            event = json.loads(raw_data)
            if event['Type'] == 'container' and event['Action'] == 'start':
                self.__logger.debug(json.dumps(event, indent=4))
                self.attacher_container(event)

    def attacher_container(self, event):
        container_id = event['id']
        attributes = event['Actor']['Attributes']
        ipv6_network = attributes.get('ipv6.mapper.network')
        if ipv6_network is not None:
            container_name = attributes['name']
            network_info = self.get_network(ipv6_network)

            ipv6_address_suffix = attributes.get('ipv6.mapper.suffix')
            if ipv6_address_suffix is None:
                # Generer un suffixe avec md5
                ipv6_address_suffix = self.hash_container(container_name)

            prefixe = network_info['prefix']
            adresse = '%s:%s' % (prefixe, ipv6_address_suffix)
            self.__logger.info("Attache container %s a l'adresse %s" % (container_id, adresse))

            network = network_info['network']
            network.connect(container_id, ipv6_address=adresse)

    def exposer_ports_container(self, container_id):
        container = self.__docker.containers.get(container_id)
        port_bindings = container.attrs['HostConfig']['PortBindings']
        for port_protocol, mappings in port_bindings.items():
            port = port_protocol.split('/')[0]
            protocol = port_protocol.split('/')[1]
            self.__logger.debug("Exposer port %s %s" % (protocol, port))

    def hash_container(self, container_name):
        m = hashlib.md5()

        split_name = container_name.split('.')
        if len(split_name) == 3:
            # Container dans un service, on garde "nom_service.numero_service"
            container_name = '.'.join(split_name[0:2])

        m.update(container_name.encode('utf-8'))
        digest = m.digest()

        # Garder les 48 premiers bits pour completer le reseau (/80)
        suffixe_str = binascii.hexlify(digest).decode('utf-8')
        suffixe_format = '%s:%s:%s' % (suffixe_str[0:2], suffixe_str[2:4], suffixe_str[4:6])
        return suffixe_format

    def get_network(self, name: str):
        network = self.__docker.networks.get(name)
        self.__logger.debug(json.dumps(network.attrs, indent=4))

        ipv6_network = network.attrs['IPAM']['Config'][1]['Subnet']
        self.__logger.debug("Elem: %s" % str(ipv6_network))
        ipv6_prefix = ipv6_network.split('/')[0][:-2]
        ipv6_len = ipv6_network.split('/')[1]

        self.__logger.debug("IPV6 Network : %s / %s" % (ipv6_prefix, ipv6_len))
        return {'network': network, 'prefix': ipv6_prefix, "len": ipv6_len}

    def parse(self):
        parser = argparse.ArgumentParser(description="Mappeur IPV6 pour docker", epilog="""
        Demarrer l'utilitaire en arriere plan (background) et configurer vos containers/services
        dans docker avec le libelle suivant:

        -"ipv6.mapper.network"="...nom_reseau_docker..."

        Pour figer le suffixe IPv6, utiliser:

        -"ipv6.mapper.suffix"="...suffixe_ipv6..."

        Note: Par defaut le nom du container est hache pour generer un suffixe stable.
        """)

        parser.add_argument(
            '--info', action="store_true", required=False,
            help="Active le logging info"
        )
        parser.add_argument(
            '--debug', action="store_true", required=False,
            help="Active le logging maximal"
        )
        parser.add_argument(
            '-d', action="store_true", required=False,
            help="Execute en arriere plan"
        )

        self.args = parser.parse_args()

        if self.args.debug:
            self.__logger.setLevel(logging.DEBUG)
        elif self.args.info:
            self.__logger.setLevel(logging.INFO)

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        src:
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

    def start(self):
        mapper.daemonize()
        mapper.run()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        self.events()


if __name__ == '__main__':
    logging.basicConfig()
    mapper = DockerIPV6Mapper()
    mapper.parse()

    if mapper.args.d:
        mapper.start()
    else:
        mapper.events()
