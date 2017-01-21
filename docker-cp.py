#!/usr/bin/python
""" python implementation of docker cp command

    Variant 1, the easy way using existing docker api python libs , might the
    only way I have time to do this

    Decided to do both deprecated and current copy methods depending on API
    version
"""

import docker
import json
import tarfile
from StringIO import StringIO
from optparse import OptionParser


def nice(object):
    """ debug function """
    print json.dumps(dir(object), indent=4)


class get_opts():

    def __init__():
        parser = OptionParser()
        parser.add_option("-b", "--buffer-length",
                          help="Specify buffer size, default 0",
                          dest="buffersize")
#          parser.add_options


class docker_cp():
    """ docker_cp
    python implementation of docker cp command"""
    def __init__(self):
        self.client = docker.Client(base_url='unix://var/run/docker.sock')
        self.containerid = "dca7e3edcf86"
        self.path = "/root/file"
        self.docker_version = self.client.version()['ApiVersion']
        self.client.api_version

    def copy(self):
        """ copy data from container, perform API version check and decide if
        we should use legacy copy function or current get_archive, returns raw
        data """
        if self.version_check(1.20) is True:
            response_data, stat = self.client.get_archive(self.containerid,
                                                          self.path)
            raw_data = response_data.data
            new_file = StringIO(raw_data)
            tar = tarfile.open(mode="r", fileobj=new_file)
            for member in tar.getmembers():
                member = tar.extractfile(member)
                """ obviously doing an unlimited read we will be in trouble
                here if the file is biger then available freem MEM
                """
                return member.read()

    def version_check(self, version):
        """ compare version number against actualy version used, version is
        taken from self.client.api_version, this being the curent backend
        supported version"""
        return True


if __name__ == "__main__":
    """ make sure this code is ran only when docker_cp.py is called directly,
    else this can be included as used externaly"""
    dc = docker_cp()
    data = dc.copy()
    # /tmp/temp2 will be changed to a var taken from input args and opts
    # buffering value  will be changed to a var taken from input args and opts

    with file("/tmp/temp2", "w+", buffering=4) as f:
        f.write(data)
