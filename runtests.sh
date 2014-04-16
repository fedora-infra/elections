#!/bin/bash

PYTHONPATH=fedora_elections ./nosetests \
--with-coverage --cover-erase --cover-package=fedora_elections $*
