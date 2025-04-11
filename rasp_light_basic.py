import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QShortcut
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QKeySequence

os.environ['DISPLAY'] = ':0'

# Threaded video reader
class VideoThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    
    def __init__(self, video_path):
        super().__init__()
        # Use GStreamer pipeline for hardware acceleration
        gst_pipeline = (
            f'filesrc location={video_path} ! '
            'qtdemux ! h264parse ! omxh264dec ! '
            'videoconvert ! appsink'
        )
        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        
        # Fallback to regular capture if GStreamer fails
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(video_path)
        
        self.running = True
        self.frame_buffer = None
        
    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                # Video ended, restart
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    continue
            
            # Convert OpenCV BGR to RGB (do this in the thread)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_buffer = frame_rgb
            self.frame_ready.emit(frame_rgb)
            
            # Small sleep to reduce CPU usage
            self.msleep(5)
            
    def stop(self):
        self.running = False
        self.wait()
        self.cap.release()

app = QApplication(sys.argv)

# Get screen information
screen_count = app.desktop().screenCount()
print(f"Number of screens detected: {screen_count}")

for i in range(screen_count):
    screen_geom = app.desktop().screenGeometry(i)
    print(f"Screen {i}: Geometry = {screen_geom.x()},{screen_geom.y()} {screen_geom.width()}x{screen_geom.height()}")

# OpenCV video player class with blinking functionality
class VideoPlayer(QMainWindow):
    def __init__(self, screen_num, screen_geom, video_path):
        super().__init__()
        self.setWindowTitle(f"Video Player {screen_num+1}")
        self.setGeometry(screen_geom)
        
        # Create label to display video frames
        self.video_label = QLabel(self)
        self.video_label.setGeometry(0, 0, screen_geom.width(), screen_geom.height())
        self.video_label.setAlignment(Qt.AlignCenter)
        
        # Set background color to black
        self.setStyleSheet("background-color: black;")
        
        # Create video thread
        self.video_thread = VideoThread(video_path)
        self.video_thread.frame_ready.connect(self.process_frame)
        self.video_thread.start()
        
        # Get video FPS
        self.fps = self.video_thread.cap.get(cv2.CAP_PROP_FPS)
        
        # Precompute black frame
        height = screen_geom.height()
        width = screen_geom.width()
        self.black_frame = np.zeros((height, width, 3), dtype=np.uint8)
        q_img = QImage(self.black_frame.data, width, height, width * 3, QImage.Format_RGB888)
        self.black_pixmap = QPixmap.fromImage(q_img)
        
        # Current pixmap to display
        self.current_pixmap = self.black_pixmap
        
        # Blinking control - use timer-based approach
        self.show_video = True
            
        # Set up separate timer for blinking effect
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.start(500)  # 500ms per phase (0.5 seconds)
        
        # Set up timer for display updates - higher refresh rate
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(16)  # ~60fps refresh
        
        # Add quit shortcut
        self.quit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.quit_shortcut.activated.connect(self.close)
    
    def process_frame(self, frame):
        if self.show_video:
            # Convert to QImage and then QPixmap
            h, w, ch = frame.shape
            q_img = QImage(frame.data, w, h, w * ch, QImage.Format_RGB888)
            
            # Resize to fit label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_img)
            self.current_pixmap = pixmap.scaled(
                self.video_label.width(), 
                self.video_label.height(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
    
    def toggle_blink(self):
        # Toggle blink state
        self.show_video = not self.show_video
        if not self.show_video:
            # Switch to black screen during blink phase
            self.current_pixmap = self.black_pixmap
    
    def update_display(self):
        # Display current pixmap (either video frame or black)
        self.video_label.setPixmap(self.current_pixmap)
        
    def closeEvent(self, event):
        self.blink_timer.stop()
        self.display_timer.stop()
        self.video_thread.stop()

# Path to video file
video_path = "trance1.mp4"
if not os.path.exists(video_path):
    print(f"Error: Video file '{video_path}' not found.")
    sys.exit(1)

# Create video players
test_windows = []
for i in range(screen_count):
    screen_geom = app.desktop().screenGeometry(i)
    window = VideoPlayer(i, screen_geom, video_path)
    window.setWindowFlags(Qt.FramelessWindowHint)
    window.show()
    test_windows.append(window)

sys.exit(app.exec_())

# import sys
# import os
# import cv2
# import numpy as np
# from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QShortcut
# from PyQt5.QtCore import Qt, QTimer
# from PyQt5.QtGui import QImage, QPixmap, QKeySequence

# os.environ['DISPLAY'] = ':0'

# app = QApplication(sys.argv)

# # Get screen information
# screen_count = app.desktop().screenCount()
# print(f"Number of screens detected: {screen_count}")

# for i in range(screen_count):
#     screen_geom = app.desktop().screenGeometry(i)
#     print(f"Screen {i}: Geometry = {screen_geom.x()},{screen_geom.y()} {screen_geom.width()}x{screen_geom.height()}")

# # OpenCV video player class with blinking functionality
# class VideoPlayer(QMainWindow):
#     def __init__(self, screen_num, screen_geom, video_path):
#         super().__init__()
#         self.setWindowTitle(f"Video Player {screen_num+1}")
#         self.setGeometry(screen_geom)
        
#         # Create label to display video frames
#         self.video_label = QLabel(self)
#         self.video_label.setGeometry(0, 0, screen_geom.width(), screen_geom.height())
#         self.video_label.setAlignment(Qt.AlignCenter)
        
#         # Open video file with OpenCV
#         self.cap = cv2.VideoCapture(video_path)
#         if not self.cap.isOpened():
#             print(f"Error: Could not open video file {video_path}")
#             self.close()
#             return
        
#         # Get video FPS and calculate frames per blink phase
#         self.fps = self.cap.get(cv2.CAP_PROP_FPS)
#         self.frames_per_phase = int(self.fps * 0.5)  # 0.5 second per phase
        
#         # Create black frame for blinking
#         self.black_frame = np.zeros((300, 400, 3), dtype=np.uint8)
        
#         # Set background color to black
#         self.setStyleSheet("background-color: black;")
        
#         # Blinking control
#         self.frame_counter = 0
#         self.show_video = True
            
#         # Set up timer for frame updates
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self.update_frame)
#         interval = int(1000 / self.fps)
#         self.timer.start(interval)
        
#         # Add quit shortcut
#         self.quit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
#         self.quit_shortcut.activated.connect(self.close)
        
#     def update_frame(self):
#         # Toggle state every N frames (blinking logic)
#         if self.frame_counter >= self.frames_per_phase:
#             self.show_video = not self.show_video
#             self.frame_counter = 0
        
#         if self.show_video:
#             ret, frame = self.cap.read()
#             if not ret:
#                 # Video ended, restart
#                 self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#                 ret, frame = self.cap.read()
#                 if not ret:
#                     print("Error: Cannot read frame after reset")
#                     return

#             # Convert OpenCV BGR to RGB
#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
#             # Convert to QImage and then QPixmap
#             h, w, ch = frame_rgb.shape
#             q_img = QImage(frame_rgb.data, w, h, w * ch, QImage.Format_RGB888)
#             pixmap = QPixmap.fromImage(q_img)
            
#             # Resize to fit label while maintaining aspect ratio
#             pixmap = pixmap.scaled(self.video_label.width(), self.video_label.height(), 
#                                 Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
#             # Display frame
#             self.video_label.setPixmap(pixmap)
#         else:
#             # Show black frame during blink phase
#             h, w, ch = self.black_frame.shape
#             q_img = QImage(self.black_frame.data, w, h, w * ch, QImage.Format_RGB888)
#             pixmap = QPixmap.fromImage(q_img)
#             self.video_label.setPixmap(pixmap)
        
#         self.frame_counter += 1
        
#     def closeEvent(self, event):
#         self.timer.stop()
#         self.cap.release()

# # Path to video file
# video_path = "trance1.mp4"
# if not os.path.exists(video_path):
#     print(f"Error: Video file '{video_path}' not found.")
#     sys.exit(1)

# # Create video players
# test_windows = []
# for i in range(screen_count):
#     screen_geom = app.desktop().screenGeometry(i)
#     window = VideoPlayer(i, screen_geom, video_path)
#     window.setWindowFlags(Qt.FramelessWindowHint)
#     window.show()
#     test_windows.append(window)

# sys.exit(app.exec_())
