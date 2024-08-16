#!/usr/bin/env bash
## Configure bash as default shell (cron uses /bin/sh)
SHELL=/bin/bash
echo "-------------------------"
date
echo "[process_map.sh] start"

## Get path of current file (process_map.sh) to get path of the repo and the rest of scripts
SOURCE=${BASH_SOURCE[0]}
while [ -L "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
export SCRIPT_PATH=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )

## Activate python venv with deps
echo "[process_map.sh] Activate venv"
cd $SCRIPT_PATH/../ && source ./venv/bin/activate


# Check if running
ps -aux | grep -v grep  | grep "python3 ./src/main.py -cfg ./config/config.yaml -mcfg ./config/map_config.yaml -mpath ./media/" > /dev/null
if [ $? -eq 0 ]; then
  echo "[process_map.sh] Process is already running :)"
else
  ## Run checkin with input options
  echo "[process_map.sh] Run script"
  cd $SCRIPT_PATH/../ && ./src/main.py "$@" -cfg ./config/config.yaml -mcfg ./config/map_config.yaml -mpath ./media/
fi



echo "[process_map.sh] end"
date
echo "-------------------------"