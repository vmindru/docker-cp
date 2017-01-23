""" docker-cp
python implementation of docker cp command
"""

from docker import Client as docker_Client
from json import dumps as json_dumps
import tarfile
from sys import exit
from os import path
from optparse import OptionParser
from StringIO import StringIO
# from time import sleep


def nice(object):
    """ debug function """
    print json_dumps(dir(object), indent=4)


class get_opts():
    def __init__(self):
        version = 0.1
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
    def __init__(self, source, dest, buffsize):
        self.client = docker_Client(base_url='unix://var/run/docker.sock')
        """ i know the bellow requirement for source and dest to be a list is
         dirty and has t be corrected """
        self.containerid = source[0]
        self.target_path = source[1]
        self.local_path = dest[0]
        self.buffsize = buffsize
        self.docker_version = self.client.version()['ApiVersion']
        self.client.api_version

    def copy_from(self):
        """ copy data from container, perform API archive call,we will not
        handle archive untar in version 0.1 data """
        response_data, stat = self.client.get_archive(self.containerid,
                                                      self.target_path)
        if path.isdir(self.local_path):
            self.dest = self.local_path+stat['name']+'.tar'
        else:
            self.dest = self.local_path+'.tar'
        # progress, buf, got_header, counter = 0, 0, False, 0
        tarfile.open(mode="r|",
                     fileobj=StringIO(response_data)
                     ).extractall()

        """ not sure how to efficiently untar in memory without reding entire
        tar, i guess i could find tar specifications read N amount of some sort
        of metadata header size, that defined start,end and name of a member
        and then extract data with seak and read similar to above.
        Bellow is simple ugly method with untar in memory"""
#        new_file = StringIO(response_data.data)
#        tar = tarfile.open(mode="r", fileobj=new_file)
#        for member in tar.getmembers():
#            member = tar.extractfile(member)
#            buf = '0'
#            while buf != '':
#                buf = member.read(4)
#                print buf

    def block_read(self, file, blocksize):
        while True:
            block = file.read(blocksize)
            if not block:
                break
            yield block

    def copy_to(self):
        """ I don't want atm to handle taring of files in memorry, version 0.1
        will asume we have already an archive"""
        try:
            tarfile.open(self.local_path, mode="r")
        except:
            print "Can not open {} archive".format(self.local_path)
            exit(1)
        with file(self.local_path, mode="r", buffering=4) as f:
            self.client.put_archive(self.containerid, self.target_path,
                                    data=self.block_read(f, self.buffsize))

    def version_check(self, version):
        """ compare version number against actualy version used, version is
        taken from self.client.api_version, this being the curent backend
        supported version"""
        return True


if __name__ == "__main__":
    """ make sure this code is ran only when docker_cp.py is called directly,
    else this can be included as used externaly"""
    opts = get_opts()
    buffsize = opts.options.buffersize
    if opts.copy_from_cont is True and opts.copy_to_cont is False:
        cp = docker_cp(opts.arg1, opts.arg2, buffsize)
        cp.copy_from()
    elif opts.copy_to_cont is True and opts.copy_from_cont is False:
        cp = docker_cp(opts.arg2, opts.arg1, buffsize)
        cp.copy_to()
