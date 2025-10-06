import sys
import os
import cv2
import numpy as np
import random
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QShortcut
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QKeySequence


# Import the MidiReceiver
from receiver import MidiReceiver


os.environ['DISPLAY'] = ':0'


# VideoThread with random start position
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

        # Randomize starting position
        if self.cap.isOpened():
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames > 0:
                random_frame = random.randint(0, total_frames - 1)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame)

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


# VideoPlayer with MIDI handling and randomized blink patterns
class VideoPlayer(QMainWindow):
    def __init__(self, screen_num, screen_geom, video_path):
        super().__init__()
        self.setWindowTitle(f"Video Player {screen_num+1}")
        self.setGeometry(screen_geom)
        self.video_enabled = True
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
        self.blink_timer.start(100)  # 500ms per phase (0.5 seconds)

        # Set up timer for display updates - higher refresh rate
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(16)  # ~60fps refresh

        # Randomization timer - every 2 minutes 30 seconds
        self.randomize_timer = QTimer(self)
        self.randomize_timer.timeout.connect(self.randomize_blink_pattern)
        self.randomize_timer.start(150000)  # 150000ms = 2.5 minutes

        # Add quit shortcut
        self.quit_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.quit_shortcut.activated.connect(self.close)

        # Add MIDI receiver
        self.midi_receiver = MidiReceiver(callback=self.handle_midi)
        self.midi_receiver.start()

        # MIDI control state
        self.blink_enabled = True

        # Initialize random blink pattern
        self.randomize_blink_pattern()

    def randomize_blink_pattern(self):
        """Randomize blink behavior every 2.5 minutes"""
        if self.blink_enabled and self.video_enabled:
            # Random pattern: sometimes blinks a lot, sometimes doesn't
            pattern_type = random.choice(['fast', 'slow', 'off', 'medium'])

            if pattern_type == 'fast':
                # Fast blinking (50-150ms)
                interval = random.randint(50, 150)
            elif pattern_type == 'medium':
                # Medium blinking (200-400ms)
                interval = random.randint(200, 400)
            elif pattern_type == 'slow':
                # Slow blinking (500-1000ms)
                interval = random.randint(500, 1000)
            else:  # 'off'
                # Stop blinking for this period
                self.blink_timer.stop()
                self.show_video = True
                return

            self.blink_timer.setInterval(interval)
            if not self.blink_timer.isActive():
                self.blink_timer.start()

    # Add MIDI handler method
    def handle_midi(self, msg):
        if msg["type"] == "note_on":
            note_data = msg["data"]

            # Toggle video with Pad 5 (note 40)
            if note_data['note'] == 40:
                self.video_enabled = not self.video_enabled

                if not self.video_enabled:
                    # Turn off video - black screen
                    self.show_video = False
                    self.blink_timer.stop()
                    self.current_pixmap = self.black_pixmap
                else:
                    # Restore video with previous blink settings
                    self.show_video = True
                    if self.blink_enabled and not self.blink_timer.isActive():
                        self.blink_timer.start()

        elif msg["type"] == "control_change":
            cc_data = msg["data"]
            if cc_data["control"] == 70 and cc_data["channel"] == 0:
                value = cc_data["value"]

                if value == 0:
                    self.blink_enabled = False
                    self.blink_timer.stop()
                    if self.video_enabled:
                        self.show_video = True
                else:
                    self.blink_enabled = True
                    interval = 500 - (value * 3.5)
                    interval = max(50, int(interval))
                    self.blink_timer.setInterval(interval)

                    if self.video_enabled and not self.blink_timer.isActive():
                        self.blink_timer.start()

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
        self.randomize_timer.stop()
        self.video_thread.stop()
        self.midi_receiver.stop()  # Stop MIDI receiver on close


# Main program
def main():
    app = QApplication(sys.argv)


    # Get screen information
    screen_count = app.desktop().screenCount()
    print(f"Number of screens detected: {screen_count}")


    for i in range(screen_count):
        screen_geom = app.desktop().screenGeometry(i)
        print(f"Screen {i}: Geometry = {screen_geom.x()},{screen_geom.y()} {screen_geom.width()}x{screen_geom.height()}")


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


if __name__ == "__main__":
    main()
