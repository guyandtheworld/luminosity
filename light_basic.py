import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QShortcut
from PyQt5.QtGui import QImage, QPixmap, QKeySequence

class VideoPlayer(QMainWindow):
    def __init__(self, video_path, x_offset, y_offset):
        super().__init__()
        # Set the window to frameless to remove window decorations
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(x_offset, y_offset, 1920, 1080)
        self.setWindowTitle("Frame-Accurate Blinking Video")

        # Video properties
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print(f"Error: Unable to open video file: {video_path}")
            sys.exit()

        # Get video FPS and calculate frames per blink phase
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frames_per_phase = int(self.fps * 0.5)  # 1 second per phase at native FPS
        
        # Get video dimensions
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create black frame at the fullscreen resolution (not the video resolution)
        self.black_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        
        # Set background color to black
        self.setStyleSheet("background-color: black;")
        
        # Display components
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)  # Center the content
        self.label.setGeometry(0, 0, 1920, 1080)
        
        # Animation control
        self.frame_counter = 0
        self.show_video = True
        
        # Frame update timer (uses video's native timing)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        interval = int(1000 / self.fps)  # Convert FPS to ms interval
        self.timer.start(interval)

        self.quit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.quit_shortcut.activated.connect(self.close)
        self.quit_shortcut.activated.connect(QApplication.quit)

    def key_press_event(self, event):
        if event.key() == Qt.Key_Escape:
            print("Escape key pressed - attempting to quit")  # Debug output
            self.close()
            QApplication.quit()  # More forceful quit

    # Also add this method to ensure close events are properly handled
    def closeEvent(self, event):
        print("Close event received")  # Debug output
        QApplication.quit()
        event.accept()

    def update_frame(self):
        # Toggle state every N frames (1 second)
        if self.frame_counter >= self.frames_per_phase:
            self.show_video = not self.show_video
            self.frame_counter = 0
        
        if self.show_video:
            ret, frame = self.cap.read()
            if not ret:  # Loop video
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Cannot read frame after reset")
                    return
                    
            # Convert frame to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Scale the frame to fit the screen while maintaining aspect ratio
            scale_width = 1920 / self.video_width
            scale_height = 1080 / self.video_height
            scale = min(scale_width, scale_height)
            
            new_width = int(self.video_width * scale)
            new_height = int(self.video_height * scale)
            
            # Resize the frame
            if new_width != self.video_width or new_height != self.video_height:
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Create a black canvas the size of the screen
            screen_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
            # Calculate position to center the video on the screen
            x_offset = (1920 - new_width) // 2
            y_offset = (1080 - new_height) // 2
            
            # Place the resized video on the canvas
            screen_frame[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = frame
            
            # Convert and display frame
            h, w, ch = screen_frame.shape
            q_image = QImage(screen_frame.data, w, h, w*ch, QImage.Format_RGB888)
            
        else:
            # Use pre-created black frame
            q_image = QImage(self.black_frame.data, 1920, 1080, 1920*3, QImage.Format_RGB888)

        self.label.setPixmap(QPixmap.fromImage(q_image))
        self.frame_counter += 1

if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_path = "test1.mp4"
    
    player1 = VideoPlayer(video_path, 1728, 37)
    player2 = VideoPlayer(video_path, 3648, 37)
    
    # Use showFullScreen() instead of show()
    player1.showFullScreen()
    player2.showFullScreen()
    
    sys.exit(app.exec_())
