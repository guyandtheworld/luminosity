from screeninfo import get_monitors

monitors = get_monitors()
for i, monitor in enumerate(monitors):
    print(f"Monitor {i}: {monitor}")



from PyQt5.QtWidgets import QApplication
import sys


import os
os.environ['DISPLAY'] = ':0'

# Create application instance if one doesn't exist yet
app = QApplication.instance() or QApplication(sys.argv)

# Get screen information
screens = app.screens()
for i, screen in enumerate(screens):
    geometry = screen.geometry()
    print(f"Screen {i}:")
    print(f"  Name: {screen.name()}")
    print(f"  Size: {geometry.width()}x{geometry.height()}")
    print(f"  Position: {geometry.x()},{geometry.y()}")
    print(f"  Physical size: {screen.physicalSize().width()}x{screen.physicalSize().height()} mm")
    print(f"  Refresh rate: {screen.refreshRate()} Hz")