""" docker-cp
python implementation of docker cp command
"""

from docker import Client as docker_Client
from json import dumps as json_dumps
import tarfile
from sys import exit
from os import path
from optparse import OptionParser
# from StringIO import StringIO
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
        parser.add_option("-c", "--create-archive",
                          help="when specified together with copy from target"
                          "container will create tar archive. Has no effect"
                          "on copy from local path  to container",
                          action="store_true",
                          default=False,
                          dest="create_archive")
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
    def __init__(self, source, dest, buffsize, archive=False):
        self.client = docker_Client(base_url='unix://var/run/docker.sock')
        """ i know the bellow requirement for source and dest to be a list is
         dirty and has t be corrected """
        self.containerid = source[0]
        self.target_path = source[1]
        self.local_path = dest[0]
        self.buffsize = buffsize
        self.docker_version = self.client.version()['ApiVersion']
        self.client.api_version
        self.create_archive = archive

    def copy_from(self):
        """ copy data from container, perform API archive call,we will not
        handle archive untar in version 0.1 data """
        response_data, stat = self.client.get_archive(self.containerid,
                                                      self.target_path)
        if path.isdir(self.local_path):
            self.dest = self.local_path+stat['name']+'.tar'
        else:
            self.dest = self.local_path+'.tar'
        if self.create_archive is False:
            tarfile.open(mode="r|",
                         fileobj=response_data).extractall(path=self.local_path)
        elif self.create_archive is True:
            buf = 0
            with file(self.dest, "w+", buffering=self.buffsize) as f:
                while buf != '':
                    buf = response_data.read(self.buffsize)
                    f.write(buf)
        else:
            print "error, invalide create_archive value"
            exit(1)

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
    create_archive = opts.options.create_archive
    if opts.copy_from_cont is True and opts.copy_to_cont is False:
        cp = docker_cp(opts.arg1, opts.arg2, buffsize, create_archive)
        cp.copy_from()
    elif opts.copy_to_cont is True and opts.copy_from_cont is False:
        cp = docker_cp(opts.arg2, opts.arg1, buffsize)
        cp.copy_to()
