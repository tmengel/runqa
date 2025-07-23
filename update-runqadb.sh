#!/bin/bash
[[ -e updaterunning ]] && exit 0
echo $$ > updaterunning
source /opt/sphenix/core/bin/sphenix_setup.sh -n
perl updateruns.pl >& /sphenix/u/sphnxpro/updateruns.log
rm updaterunning
