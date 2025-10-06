# README.md

* Use SSH to connect to the pi `ssh dharze@dpi1.local` or `ssh dharze@dp21.local`
* If on a new network, connect to hotspot (Adarsh), and then connect both devices to the new wifi. 
* If the pi was wiped, you need to configure `sudo raspi-config` to turn on VNC
* `sudo poweroff` to shutdown the pi
* add `ssh dharze@dpi1.local` on vscode

# Pi Specific
* To install use `sudo apt install python3-screeninfo` for system-wide install. 
* `sudo apt install python3-opencv` and `sudo apt install python3-pyqt5` and `sudo apt install python3-websockets`
* Run the `screen_resolution.py` script to get the resolution. 
* Auto hide taskbar
* Copy video to file `scp trance1.mp4 dharze@dpi1.local:`
```
Code: Select all

mousepad .config/wf-panel-pi.ini
add:
Code: Select all

# automatically hide when pointer isn't over the panel
autohide = true
# time in milliseconds to wait before hiding
autohide_duration = 500
# layer can be top, bottom, overlay or background
layer = top
```

Command to run at start up

* Create Luminosity/startup.log
* touch at room start_up.sh
* Add

```
#!/bin/bash

LOG_FILE=~/Luminosity/startup.log

echo "=== Script started at $(date) ===" >> $LOG_FILE
echo "Current user: $(whoami)" >> $LOG_FILE
echo "Current directory: $(pwd)" >> $LOG_FILE

echo "Waiting 60 seconds..." >> $LOG_FILE
sleep 60

echo "Sleep completed at $(date)" >> $LOG_FILE
echo "Changing to ~/Luminosity directory..." >> $LOG_FILE

if cd ~/Luminosity; then
    echo "Successfully changed to $(pwd)" >> $LOG_FILE
    echo "Running Python script..." >> $LOG_FILE
    python3 light_basic.py >> $LOG_FILE 2>&1
    echo "Python script finished with exit code: $?" >> $LOG_FILE
else
    echo "ERROR: Failed to change to ~/Luminosity directory" >> $LOG_FILE
    echo "Directory does not exist or no permissions" >> $LOG_FILE
    exit 1
fi

echo "=== Script completed at $(date) ===" >> $LOG_FILE
```

* Make it executable chmod +x start_up.sh
* Add /home/dharze/start_up.sh to .bashrc
* Remove any remnants from crontab or /etc/rc.local