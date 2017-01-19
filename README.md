# docker-cp


Write an implementation of `docker cp` command. That is, a command that copies
a file from or to a specified container using a fixed size buffer. The
solution we're looking for shouldn't need to create any temporary file in the
container, start any new processes in the container, nor export the entire
container file system during the write. Use Python for the implementation,
using SDK like docker-py is allowed as long as the latest version is used, and
only functions that haven't been deprecated or obsoleted are used. Executing
`docker` commands isn't allowed.

## An example run of the command should look like this:

```
$ docker run -d --name test fedora:25 /usr/bin/sleep
293f80ab6d2bf57e85a6d10762b3cc795cdb104a152d0257471b63544e093166
$ docker-cp --bufer-length=4 test:/etc/fedora-release .
$ cat fedora-release
Fedora release 25 (Twenty Five)
```
