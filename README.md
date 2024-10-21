# Temperature and Humidity Map Tracker

This script subscribes to a set of MQTT topics published by HomeAssistant and projects temperature and humidity measures over an image (suposedly a map).

## Requirements

The script is supposed to run under a Linux environment making use of Python3.

## Installation

All the process can be done into a virtual environment. But for some reason with cmake opencv cannot be installed with pip, install with apt and make sure the venv can work with it. Then make the venv inherit the system packages:

```sh
    sudo apt install python-opencv
```

Create the venv inheriting from system and activate it with the following commands (or just ignore these an execute without venv):

```sh
    python3 -m venv --system-site-packages venv
    source venv/bin/activate
```

The environment can be deactivated as follows:
```sh
    deactivate
```

Clone the repository in a given location and install its requirementes with the following command, executed from the root folder of the repository. You can check the requirements file to check the libraries that will be installed into your system.

```sh
    pip3 install --upgrade pip setuptools wheel
    pip3 install -r requirements 
```


## Configuration

Sensitive information is stored in a config file to avoid it in the code. This information is enconded into a `YAML` file.

The config file is provided to the script through an argument and should contain the folloging information:

```YML
    mqtt_host: '**********'
    client_name: "**********"
    hostname: 'homeassistant.local'
    mqtt_port: 1883
    timeout: 60

    mqtt_username: "**********"
    mqtt_password: "**********"

    config: "./config/config.yaml"
    ntfy_topic: "topic_name"
    log_path: "./logs"
```

Note that `ntfy_topic` can be set as `None` to completely deactivate push notifications.

The default config file is set to be in `./config/config.yaml`. If no argument is provided this is what should be looked for.

## Execution


There are different scripts to be used:
```
usage: main.py [-h] 

Automatic checkin in UMH time monitoring system

optional arguments:
  -h, --help            show this help message and exit
  -cfg CONFIG, --config CONFIG
                        Configuration file with user and topic. Default is set to config.yaml

```

## Automatización en crontab

### Loading cronjobs file

The file `cronjobs` in `config` folder can be edited and loaded to crontab to be used. To load any file to crontab just execute `crontab filename` and it will be loaded. In case more files need to be loaded the following command can be executed (in case all the files are called `cronjobs`):

```sh
    find . -name "cronjobs" | xargs cat  | crontab -
```

The command `crontab -l` can be used to chceck if the cron jobs were loaded correctly.

### Loading cron making use of interface
Making use of crontab the script can be executed every hour. Open crontab config file with the following command:

```sh
    crontab -e
```


To configure this setup these following lines are to be added to the end of the cron file:
```
*/20 * * * * /home/pi/tem_hum_map_tracker/scripts/track.sh >> /home/pi/tem_hum_map_tracker/logs/log_crontab.log 2>&11
00 23 * * 0 (cd /home/pi/tem_hum_map_tracker/logs && rm log_crontab.log map_generation_log.log )
```

> Nota: Making use of shell script `track.sh` the activation of the env is already handled. It also sotres a log file of the terminal output in case it is needed to check it.
