import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import cv2
import shutil


def make_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def remove_folder(folder):
    if os.path.exists(folder) and os.path.isdir(folder):
        shutil.rmtree(folder)


def video_duration(file):
    video = cv2.VideoCapture(file)
    fps = video.get(cv2.CAP_PROP_FPS)  # OpenCV v2.x used "CV_CAP_PROP_FPS"
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    video.release()
    return duration


def trim_video(video, file_name, start, end):
    clip = VideoFileClip(video)
    clip_no_sound = clip.without_audio()
    clip1 = clip_no_sound.subclip(start, end)
    clip1.write_videofile(file_name, codec='libx264')
    clip.close()


def generate_thumbnail(file, position, destination_folder, destination_file):
    make_folder(destination_folder)
    vidcap = cv2.VideoCapture(file)

    print("Started generating the thumbnail")

    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    frame_count = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    frame = int(frame_count * position)
    res, im_ar = vidcap.read()

    count = 0

    while count < frame:
        res, im_ar = vidcap.read()
        count += 1

    im_ar = cv2.resize(im_ar, (width, height), 0, 0, cv2.INTER_LINEAR)
    cv2.imwrite(destination_folder + destination_file, im_ar)

    print("Successfully generated", destination_folder + destination_file)


def combine_videos(clip_paths, destination, file_name):
    clips = [VideoFileClip(c) for c in clip_paths]
    make_folder(destination)
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(destination + file_name)
    for clip in clips:
        clip.close()


def generate_preview(file, duration, destination_folder, destination_file):
    dirpath = destination_folder + "temp"
    make_folder(dirpath)
    make_folder(destination_folder)

    for i in range(10):
        fraction = i / 10
        trim_video(file, destination_folder + 'temp/edited_%s.mp4' % i, duration * fraction, (duration * fraction) + 1)

    combine_videos(
        (destination_folder + "temp/edited_%s.mp4" % s for s in range(10)),
        destination_folder, destination_file)

    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        shutil.rmtree(dirpath)

