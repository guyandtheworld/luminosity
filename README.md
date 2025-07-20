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
