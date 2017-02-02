""" docker-cp
    python implementation of docker cp command
    TODO: verify file names, if passing odd bytes as input,
    errors may happen
"""

from sys import exit
from os import path
from os import walk as walk_dir
from docker import Client as docker_Client
from json import dumps as json_dumps
from optparse import OptionParser
from io import BytesIO
import tarfile


def __nice__(object):
    """ debug function, this will be removed envetually"""
    print(json_dumps(dir(object), indent=4))


class get_opts():
    def __init__(self):
        version = 2.1
        usage = "usage: %prog [options] source_path, container:dest_path"
        parser = OptionParser(usage=usage, version=version)
        parser.add_option("-b", "--buffer-length",
                          help="Specify buffer size, default 0",
                          default=0,
                          type=int,
                          dest="buffersize")
        parser.add_option("-a", "--archive",
                          help="when specified together with copy from target"
                          "container will create tar archive."
                          "when specified together with copy to target "
                          "container expects input tar archive file",
                          action="store_true",
                          default=False,
                          dest="archive")
        (self.options, self.args) = parser.parse_args()
        if len(self.args) != 2:
            print("{}\nError:\n\nIncorrect arguments counts\n"
                  .format(parser.print_help()))
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
            print("{}\nError:\n\nIncorrect arguments\n{}"
                  .format(parser.print_help(), self.args))
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
        self.archive = archive

    def copy_files_from_container(self):
        """ copy data from container, optionally can save files as archive """
        response_data, response_stat = self.client.get_archive(self.containerid,
                                                               self.target_path)
        if path.isdir(self.local_path):
            self.dest = self.local_path+response_stat['name']+'.tar'
        else:
            self.dest = self.local_path+'.tar'
        if self.archive is False:
            tarfile.open(mode="r|",
                         fileobj=response_data).extractall(path=self.local_path)
            return True
        elif self.archive is True:
            buf = 0
            with open(self.dest, "w+", buffering=self.buffsize) as f:
                while buf != '':
                    buf = response_data.read(self.buffsize)
                    f.write(buf)
                return True
        else:
            print("error, invalide archive value")
            exit(1)

    def block_read(self, file, buffsize):
        """ yield data in required block size, file has to be a fileobject"""
        while True:
            # __nice__(file)
#            __nice__(file.encoding)
            block = file.read(buffsize)
            if not block:
                break
            yield block

    def listdir(self, list_path):
        """ return list of files and dirs in following order, first dirs second
        files, if not listed in this order we might endup trying to untar a
        file in a not existing location"""
        if path.isdir(list_path) is True:
            for root, dirs, files in walk_dir(list_path, topdown=True):
                for name in dirs:
                    yield path.join(root, name)
                for name in files:
                    yield path.join(root, name)
        else:
            yield list_path

    def stream_tar(self, path, buffsize):
        """ stream tar archive, use tarfile to create hte header then send file
        and at the end send footer 2x512 zeros as per tar specification,
        footer is created with tar.close()"""
        archive = BytesIO()
        tar = tarfile.open(mode="w", fileobj=archive)
        tarinfo = tar.gettarinfo(path)
        tar.addfile(tarinfo)
        archive.seek(0)
        yield archive.read()
        with open(path, mode="rb", buffering=buffsize) as file:
            while True:
                block = file.read(buffsize)
                if not block:
                    break
                yield block
        tar.fileobj.seek(0)
        tar.fileobj.truncate()
        tar.close()
        archive.seek(0)
        yield archive.read()

    def copy_files_to_container(self):
        if self.archive is True:
            try:
                tarfile.open(self.local_path, mode="rb")
            except:
                print("Can not open {} archive".format(self.local_path))
                exit(1)
            with open(self.local_path, mode="rb", buffering=self.buffsize) as f:
                self.client.put_archive(self.containerid, self.target_path,
                                        data=self.block_read(f, self.buffsize))
        elif self.archive is False:
            """ send files 1 at a time """
            for file in self.listdir(self.local_path):
                self.client.put_archive(self.containerid, self.target_path,
                                        data=self.stream_tar(file,
                                                             self.buffsize))

        else:
            print("error, invalide archive value")


if __name__ == "__main__":
    """ make sure this code is ran only when docker_cp.py is called directly,
    else this can be included as used externaly"""
    opts = get_opts()
    buffsize = opts.options.buffersize
    archive = opts.options.archive
    if opts.copy_from_cont is True and opts.copy_to_cont is False:
        cp = docker_cp(opts.arg1, opts.arg2, buffsize, archive)
        cp.copy_files_from_container()
    elif opts.copy_to_cont is True and opts.copy_from_cont is False:
        cp = docker_cp(opts.arg2, opts.arg1, buffsize, archive)
        cp.copy_files_to_container()
