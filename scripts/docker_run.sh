#!/bin/bash

[ "$DEBUG" == "1" ] && set -x

prepare_gluster.sh &
/usr/bin/supervisord