import math
import time
import traceback
import uuid
from datetime import date
import random

from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from django.template import loader
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

from .models import Video, Labels, VideoLabels, DeleteRequests
from .video_manager import *


def update_views(video_id=-1):
    """
    Update views in the labels table. This will enable to do recommendations based upon views
    :param video_id:
        -1 - (Hard update): This will check for every video and update the category accordingly.
                Used when new video is deleted or labels are changed.
        video_id - (Soft update): This will just update the rows relevant to the given video
                   Used when a video is watched.
    :return: None
    """
    if video_id == -1:
        label_ids = [elements['id'] for elements in Labels.objects.values("id")]

        for label in label_ids:
            total_views = 0
            videos = VideoLabels.objects.filter(label=label).values()
            for video in videos:
                current_video_id = video['video']
                video_obj = Video.objects.filter(id=current_video_id)
                views = video_obj.get().views
                total_views += views

            label_obj = Labels.objects.get(id=label)
            label_obj.views = total_views
            label_obj.save()
        print("Updated total views")

    else:
        vid_labels = VideoLabels.objects.filter(video=video_id).values()

        for vid_label in vid_labels:
            label_id = vid_label['label']
            label_obj = Labels.objects.get(id=label_id)
            label_obj.views += 1
            label_obj.save()


def get_label_ids(_labels):
    label_ids = []
    for curr_label in _labels:
        if curr_label != "":
            if Labels.objects.filter(label=curr_label).exists():
                label_ids.append(Labels.objects.get(label=curr_label).id)
    return label_ids


def get_set_label_ids(_labels):
    label_ids = []
    for curr_label in _labels:
        if curr_label != "":
            if Labels.objects.filter(label=curr_label).exists():
                label_ids.append(Labels.objects.get(label=curr_label).id)
            else:
                lab_obj = Labels.objects.create(label=curr_label, views=0)
                lab_obj.save()
                label_ids.append(Labels.objects.get(label=curr_label).id)

    return label_ids


def save_labels(video_id, label_ids):
    vid_label_obj = VideoLabels.objects.filter(video=video_id)
    if len(vid_label_obj) != 0:
        for curr_obj in vid_label_obj:
            curr_obj.delete()

    for curr_id in label_ids:
        vid_lbl_obj = VideoLabels.objects.create(video=video_id, label=curr_id)
        vid_lbl_obj.save()
    update_views()


def check_label_is_used(label):
    label_id = Labels.objects.get(label=label).id
    return VideoLabels.objects.filter(label=label_id).exists()


def video_object(videos, request):
    data = []
    host = request.get_host()
    for video in videos:
        data.append({
            "id": video.id,
            "title": video.title,
            "preview": host + "/" + video.prev_loc,
            "thumbnail": host + "/" + video.thumb_loc,
            "length": video.length,
            "views": video.views
        })
    return data


def video_sets_creator(videos):
    data = []
    for video in videos:
        data.append((video.id, video.title, video.location, "/" + video.prev_loc, "/" + video.thumb_loc, video.date, video.length, video.views))
    return data


def recommendations_creator():
    most_viewed_labels = [label_id['id'] for label_id in Labels.objects.all().order_by('-views').values()[:3]]
    least_viewed_labels = [label_id['id'] for label_id in Labels.objects.all().order_by('views').values()[:3]]
    recommended_videos = []

    for label in most_viewed_labels:
        current_videos = VideoLabels.objects.filter(label=label)
        videos_in_the_label = [obj.video for obj in current_videos]
        random.shuffle(videos_in_the_label)

        for video in videos_in_the_label:
            if video not in recommended_videos:
                recommended_videos.append(video)
                break

    for label in least_viewed_labels:
        current_videos = VideoLabels.objects.filter(label=label)
        videos_in_the_label = [obj.video for obj in current_videos]
        random.shuffle(videos_in_the_label)

        for video in videos_in_the_label:
            if video not in recommended_videos:
                recommended_videos.append(video)
                break
    return recommended_videos


def recommendations(request):
    recommended = recommendations_creator()
    videos = []
    for video in recommended:
        videos.append(Video.objects.get(id=video))
    data_dict = {"data": video_object(videos, request)}
    return JsonResponse(data_dict)


def labels(request):
    if request.method == "GET":
        get_body = request.GET
        labels_list = get_body.getlist('labels')
        if len(labels_list) == 0 and 'video-id' not in get_body and 'remove' not in get_body:
            _labels = Labels.objects.values('label').order_by('label')
            return JsonResponse({"labels": [label['label'] for label in _labels]})

        label_ids = get_set_label_ids(labels_list)
        if 'video-id' in get_body:
            try:
                req_id = int(request.GET['video-id'])
                Video.objects.get(id=req_id)
            except ValueError:
                raise BadRequest("Invalid Request")
            except ObjectDoesNotExist:
                raise BadRequest("Invalid video id")

            print(label_ids)
            save_labels(req_id, label_ids)

            return HttpResponse("OK")

        try:
            if not check_label_is_used(request.GET['remove']):
                label = Labels.objects.get(label=request.GET['remove'])
                label.delete()
                return HttpResponse("OK")
            else:
                return HttpResponse("Label is already in use", status=400)
        except ObjectDoesNotExist:
            raise BadRequest("Invalid label to remove")
        except MultiValueDictKeyError:
            raise BadRequest()


def video_remover(vid_id):
    if Video.objects.filter(id=vid_id).exists():
        vid_labels = VideoLabels.objects.filter(video=vid_id)
        for curr_label in vid_labels:
            curr_label.delete()

        video = Video.objects.get(id=vid_id)
        video_path = os.path.dirname(video.location)[:-5]
        video.delete()
        remove_folder(video_path)
        return True
    else:
        return False


def delete_videos(request):
    if request.method == "GET":
        get_body = request.GET
        if 'video-id' in get_body:
            unique_id = str(uuid.uuid4().hex)
            seconds = int(time.time())

            try:
                req_id = int(get_body['video-id'])
            except ValueError:
                raise BadRequest("Invalid video id")

            del_req = DeleteRequests(unique_id, req_id, seconds)
            del_req.save()

            return JsonResponse({"videoId": req_id, "requestId": unique_id})
        elif 'request-id' in get_body:
            conf_id = get_body['request-id']
            if DeleteRequests.objects.filter(confirmation_id=conf_id).exists():
                del_req = DeleteRequests.objects.get(confirmation_id=conf_id)
                vid_id = del_req.video
                elapsed_time = int(time.time()) - int(del_req.requested_millis)

                if elapsed_time < 120:
                    if video_remover(vid_id):
                        update_views()
                        return JsonResponse({"status": "OK"})
                    else:
                        return JsonResponse({"status": "Failed"}, status=400)

                else:
                    return JsonResponse({"status": "TimeOut"}, status=400)

            else:
                raise BadRequest("Invalid request id")

        else:
            raise BadRequest("'video-id' not found")


def get_video_labels(video_id):
    label_ids = [obj.label for obj in VideoLabels.objects.filter(video=video_id)]
    _labels = [Labels.objects.get(id=obj).label for obj in label_ids]
    return _labels


@csrf_exempt
def say_hello(request):
    return HttpResponse(loader.get_template('index.html').render())


@csrf_exempt
def upload(request):
    if request.method == "POST":
        uploaded_files = request.FILES.getlist("file")
        vid_labels = request.POST.getlist('labels')

        if len(uploaded_files) == 0:
            return HttpResponse("InvalidRequest")

        failed_files = {}
        succeeded = {}

        for curr_file in uploaded_files:
            fs = FileSystemStorage()
            print(date.today())

            file_name = curr_file.name
            file_type = curr_file.content_type.split('/')[0]

            if len(uploaded_files) == 1:
                try:
                    video_title = request.POST.getlist('name')[0]
                except IndexError:
                    video_title = file_name.split('.')[0]

                if video_title == "":
                    video_title = file_name.split('.')[0]
            else:
                video_title = file_name.split('.')[0]

            unique_filename = str(uuid.uuid4().hex)

            path = "media/videos/" + unique_filename

            if file_type != "video":
                failed_files[file_name] = "InvalidType"
                remove_folder(path)
                continue

            file_ext = str(file_name).split('.')[-1]

            _file = "media/videos/%s/video/" % unique_filename + unique_filename + "." + file_ext
            file_media_path = "videos/%s/video/" % unique_filename + unique_filename + "." + file_ext

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
                    title=video_title,
                    location=_file,
                    prev_loc="media/videos/%s/preview/%s" % (unique_filename, "preview.mp4"),
                    thumb_loc="media/videos/%s/thumbnail/%s" % (unique_filename, "thumbnail.jpg"),
                    views=0,
                    length=int(duration)
                )
                video.save()

                vid_id = video.id
                label_ids = get_set_label_ids(vid_labels)

                save_labels(vid_id, label_ids)
                succeeded[vid_id] = video_title

            except:
                print("Database failed")
                remove_folder(path)
                traceback.print_exc()

        return JsonResponse({
            "failedFiles": failed_files,
            "succeeded": succeeded
        })
    else:
        return HttpResponse("what is this")


def paged_video_data(videos, request, page=-1, no_of_videos=15):
    max_videos = len(videos)
    starting_index = 0 if page == -1 else (page - 1) * no_of_videos
    ending_index = max_videos if page == -1 else page * no_of_videos
    data_dict = {"data": [], "pages": int(math.ceil(max_videos / no_of_videos))}
    host = request.get_host()
    for row in videos[starting_index:ending_index]:
        data_dict['data'].append({
            "id": row[0],
            "title": row[1],
            "preview": host + "/" + row[3],
            "thumbnail": host + "/" + row[4],
            "length": row[6],
            "views": row[7]
        })
    return data_dict


def get_all_videos(request):
    if request.method == "GET":
        get_body = request.GET
        if 'video-id' in get_body:
            try:
                req_id = int(get_body['video-id'])
                video_obj = Video.objects.get(id=req_id)
            except ValueError:
                raise BadRequest("Invalid Request")
            except ObjectDoesNotExist:
                raise BadRequest("Invalid video id")

            video_obj.views += 1
            update_views(int(request.GET['video-id']))
            video_obj.save()

            return JsonResponse(
                {
                    "title": video_obj.title,
                    "url": request.get_host() + "/" + str(video_obj.location),
                    "views": video_obj.views,
                    "date": video_obj.date,
                    "labels": get_video_labels(video_obj.id)
                }
            )

        max_amount = 15

        if 'max' in get_body:
            try:
                max_amount = int(get_body['max']) if int(get_body['max']) > 0 else 15
            except ValueError:
                max_amount = 15

        if 'page' in get_body:
            try:
                page = int(get_body['page'])
                if page < 1:
                    raise BadRequest("Invalid page number")
                return JsonResponse(
                    paged_video_data(Video.objects.values_list(), request, page, no_of_videos=max_amount))
            except ValueError:
                raise BadRequest("Invalid page number")

        return JsonResponse(paged_video_data(Video.objects.values_list(), request))


def search(request):
    if request.method == "GET":
        get_body = request.GET
        page = 1
        if 'filter' not in get_body and 'q' not in get_body:
            raise BadRequest("Invalid Request")
        query = ""
        if 'q' in get_body:
            query = get_body['q']

        max_amount = 15

        if 'max' in get_body:
            try:
                max_amount = int(get_body['max']) if int(get_body['max']) > 0 else 15
            except ValueError:
                max_amount = 15

        if 'page' in get_body:
            try:
                page = int(get_body['page'])
                if page < 1:
                    raise BadRequest("Invalid page number")

            except ValueError:
                raise BadRequest("Invalid page number")

        filters = request.GET.getlist('filter')
        print(filters)
        videos = Video.objects.filter(title__contains=query)
        if len(filters) == 0:
            data_dict = paged_video_data(video_sets_creator(videos), request, page, max_amount)
            return JsonResponse(data_dict)
        for _filter in filters:
            if not Labels.objects.filter(label=_filter).exists():
                return HttpResponse("Invalid filter", status=400)

        label_ids = get_label_ids(filters)
        filtered_videos = []
        filtered_videos_obj = []
        for label_id in label_ids:
            video_ids = [curr_id['video'] for curr_id in VideoLabels.objects.filter(label=label_id).values('video')]
            filtered_videos += video_ids
        for video in videos:
            if video.id in filtered_videos:
                filtered_videos_obj.append(video)

        data_dict = paged_video_data(video_sets_creator(filtered_videos_obj), request, page, max_amount)
        return JsonResponse(data_dict)
