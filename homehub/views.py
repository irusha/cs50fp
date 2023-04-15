import traceback
import uuid
from datetime import date

from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

from .models import Video
from .video_manager import *
from django.db import models


class Labels(models.Model):
    label = models.CharField(max_length=50)
    views = models.IntegerField()


def remove_folder(folder):
    if os.path.exists(folder) and os.path.isdir(folder):
        shutil.rmtree(folder)


@csrf_exempt
def say_hello(request):
    print(request.FILES)
    return HttpResponse('hello world')


@csrf_exempt
def upload(request):
    if request.method == "POST":
        uploaded_files = request.FILES.getlist("file")

        if len(uploaded_files) == 0:
            return HttpResponse("InvalidRequest")

        failed_files = {}

        for curr_file in uploaded_files:
            fs = FileSystemStorage()
            print(date.today())

            file_name = curr_file.name
            file_ext = str(file_name).split('.')[-1]

            unique_filename = str(uuid.uuid4().hex)

            _file = "media/videos/%s/video/" % unique_filename + unique_filename + "." + file_ext
            file_media_path = "videos/%s/video/" % unique_filename + unique_filename + "." + file_ext

            path = "media/videos/" + unique_filename

            file_type = curr_file.content_type.split('/')[0]

            if file_type != "video":
                failed_files[file_name] = "InvalidType"
                remove_folder(path)
                continue

            make_folder("media/videos/%s/video/" % unique_filename)
            fs.save(file_media_path, curr_file)

            try:
                duration = video_duration(_file)
            except:
                failed_files[file_name] = "ParseError"
                remove_folder(path)
                continue

            if duration < 15:
                failed_files[file_name] = "ShortVideo"
                remove_folder(path)
                continue

            try:
                generate_thumbnail(_file, 0.2, "media/videos/%s/thumbnail/" % unique_filename, "thumbnail.jpg")
                generate_preview(_file, duration, "media/videos/%s/preview/" % unique_filename, "preview.mp4")

            except:
                failed_files[file_name] = "ParseError"
                remove_folder(path)
                continue

            try:
                video = Video.objects.create(
                    title=file_name,
                    location=_file,
                    prev_loc="media/videos/%s/preview/%s" % (unique_filename, "preview.mp4"),
                    thumb_loc="media/videos/%s/thumbnail/%s" % (unique_filename, "thumbnail.jpg"),
                    views=0,
                    length=int(duration)
                )
                video.save()

            except:
                print("Database failed")
                traceback.print_exc()

        return JsonResponse({
            "failed_files": failed_files
        })
    else:
        return HttpResponse("what is this")


def get_all_videos(request):
    if request.method == "GET":
        get_body = request.GET
        if 'video-id' in get_body:
            try:
                req_id = int(request.GET['video-id'])
                video_obj = Video.objects.get(id=req_id)
            except ValueError:
                raise BadRequest("Invalid Request")
            except ObjectDoesNotExist:
                raise BadRequest("Invalid video id")

            return JsonResponse(
                {
                    "title": video_obj.title,
                    "url": request.get_host() + "/" + str(video_obj.location),
                    "views": video_obj.views,
                    "date": video_obj.date
                }
            )

        data_dict = {"data": []}
        for row in Video.objects.values_list():
            data_dict['data'].append({
                "id": row[0],
                "title": row[1],
                "preview": request.get_host() + "/" + row[3],
                "thumbnail": request.get_host() + "/" + row[4],
                "length": row[6],
                "views": row[7]
            })

        print(request.GET)

        return JsonResponse(data_dict)
    else:
        return HttpResponse('Post')

