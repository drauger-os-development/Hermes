# Hermes
Hermes System for Service Uptime Monitoring over the Network

The Hermes System is an Uptime Monitoring System that provides a simple REST API in order to obtain statistics from it.

## Files of Note
 - `settings.json`: General global settings, including controlling how Hermes launches in it's Virtual Environment
 - `track.json`: Control what URLs need to be tracked
 - `hermes.ini`: Control uWSGI settings for talking to NGINX

## Technologies in use
 - **Flask** is used to provide the REST API
 - The **multiprocessing** library provides the multi-threading capabilities as well as communication between processes through the `comms.py` system.
 - A **Virtual Environment** is used to help improve security and isolation


## Usage
To run Hermes locally, for testing and development purposes, run this command:
```
sudo ./hermes.py --debug
```

## NOTE
Hermes is still under active development and is not yet ready for general usage.
