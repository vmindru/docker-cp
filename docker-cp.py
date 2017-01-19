#!/usr/bin/python
""" python implementation of docker cp command

    Variant 1, the easy way using existing docker api python libs , might the
    only way I have time to do this

    Decided to do both deprecated and current copy methods depending on API
    version
"""

import docker


class self():
    client = docker.from_env()
    containerid = ""
    path = "/"
    docker_version = client.version()['ApiVersion']


def legacy_copy():
    """ not sure how portable this functions should be, will
    assume it's ok to use class vars inside here"""
    data = self.client.copy(self.contaienrid, self.path)
    return data


def copy():
    print self.path
    return


def version_check():
    return

copy()
