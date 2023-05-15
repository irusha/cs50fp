from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    prev_loc = models.CharField(max_length=100)
    thumb_loc = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    length = models.IntegerField()
    views = models.IntegerField()


class Labels(models.Model):
    label = models.CharField(max_length=50)
    views = models.IntegerField()


class VideoLabels(models.Model):
    video = models.IntegerField()
    label = models.IntegerField()


class DeleteRequests(models.Model):
    confirmation_id = models.CharField(max_length=50, primary_key=True)
    video = models.IntegerField()
    requested_millis = models.IntegerField()

