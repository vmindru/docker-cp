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
from sys import exit
from StringIO import StringIO
from optparse import OptionParser


def nice(object):
    """ debug function """
    print json.dumps(dir(object), indent=4)


class get_opts():

    def __init__(self):
        version = 1.0
        usage = "usage: %prog [options] source_path, container:dest_path"
        parser = OptionParser(usage=usage, version=version)
        parser.add_option("-b", "--buffer-length",
                          help="Specify buffer size, default 0",
                          default=0,
                          type=int,
                          dest="buffersize")
        (self.options, self.args) = parser.parse_args()
        if len(self.args) != 2:
            print "{}\nError:\n\nIncorrect arguments counts\n"\
                  .format(parser.print_help())
            exit(1)
        """ we have to make sure our arguments are correct,
        also figure out the intention to copy  from or to container"""
        self.arg1, self.arg2 = [arg.split(":") for arg in self.args]
        if len(self.arg1) == 2 and len(self.arg2) == 1:
            self.copy_from_cont = True
            self.copy_to_cont = False
        elif len(self.arg1) == 1 and len(self.arg2) == 2:
            self.copy_from_cont = False
            self.copy_to_cont = True
        else:
            print "{}\nError:\n\nIncorrect arguments\n{}"\
                  .format(parser.print_help(), self.args)
            exit(1)


class docker_cp():
    """ docker_cp
    python implementation of docker cp command"""
    def __init__(self):
        self.client = docker.Client(base_url='unix://var/run/docker.sock')
        self.containerid = "dca7e3edcf86"
        self.path = "/root/file"
        self.docker_version = self.client.version()['ApiVersion']
        self.client.api_version

    def copy_from(self):
        """ copy data from container, perform API version check and decide if
        we should use legacy copy function or current get_archive, returns raw
        data """
        if self.version_check(1.20) is True:
            pass
        else:
            print "Not supported API version"
            exit(1)
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
    opts = get_opts()
