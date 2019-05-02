#!/bin/bash

FEDORA_ELECTIONS_CONFIG=`pwd`/tests/config \
PYTHONPATH=fedora_elections python3 ./nosetests \
--with-coverage --cover-erase --cover-package=fedora_elections $*
