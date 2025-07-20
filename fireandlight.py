import sys
import os
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, vfx
from moviepy.video.fx.Resize import Resize
from moviepy.video.fx.Rotate import Rotate


import cv2


def play_loop(final_video_path):
    cap = cv2.VideoCapture(final_video_path)
    
    # Create a window and set it to full screen
    cv2.namedWindow('Triple Stream', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Triple Stream', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            
        cv2.imshow('Triple Stream', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

def overlay_rotating_image(video_path, image_path, output_path=None):
    if output_path is None:
        video_filename = video_path.split("/")[-1]
        output_path = f"output_{video_filename}"
    
    # Load video
    video = VideoFileClip(video_path)
    video_width, video_height = video.size
    
    # Load image
    image = ImageClip(image_path, transparent=True)
    
    # Calculate 20% of video size (based on width)
    target_width = int(video_width * 0.2)
    # Maintain aspect ratio
    image_aspect = image.size[0] / image.size[1]
    target_height = int(target_width / image_aspect)
    
    image = image.with_position(("center", "center"))
    
    # Set duration
    image = image.with_duration(video.duration)
    
    rotate_effect = Rotate(lambda t: 15*t)
    rotating_image = rotate_effect.apply(image)

    # Create composite
    final = CompositeVideoClip([video, rotating_image])
    
    # Write output file
    final.write_videofile(output_path)
    
    # Close clips
    video.close()
    image.close()
    final.close()
    
    return output_path

# def overlay_image_on_video(video_path, image_path, output_path=None):
#     if output_path is None:
#         video_filename = video_path.split("/")[-1]
#         output_path = f"output_{video_filename}"
    
#     video = VideoFileClip(video_path)
    
#     image = ImageClip(image_path, transparent=True)
#     image = image.with_position(("center", "center"))
#     image = image.with_duration(video.duration)
    
#     final = CompositeVideoClip([video, image])
#     final.write_videofile(output_path)
    
#     video.close()
#     image.close()
#     final.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 fireandlight.py <video_file> <image_file> [output_file]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    image_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    final_path = overlay_rotating_image(video_path, image_path, output_path)

    # overlay_image_on_video(video_path, image_path, output_path)
    play_loop("flowers.mp4")
    