# smogtok-plug
Domoticz Python SmogTok plugin

Smogtok is air quality (including smog) monitoring system, that includes:
- multiple monitoring devices
- central data aggregation server
- visualisation web application - for desktop an mobile devices
(Please contact us if needed english (or other) version of the monitoring application.
https://smogtok.com
smogtok@gmail.com)

Plugin implementaion pulls the air quailty data to your home automation system.

# How it works?

The steps performed by plugin in each retrieval interval:
- pulls the air quailty data from SmogTok server
- creates Domoticz devices - matching the input data from SmogTok
- saves received data value to the devices

Data is get from SmogTok:
- for probe id entered as a hardware parameter
- from the nearest geografically probe - from localization settings

# Installation 
To install a plugin:
- get plugin.py file and install like any other python plugin (https://www.domoticz.com/wiki/Using_Python_plugins)
- get if using Domoticz Python plugin manager (https://www.domoticz.com/wiki/Python_Plugin_Manager)



# TODO:
 - ....

# Notes

BEWARE, this is a very early version. Use it on your test server first.
Waiting for your comments!!!!
