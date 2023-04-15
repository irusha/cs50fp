from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    prev_loc = models.CharField(max_length=100)
    thumb_loc = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    length = models.IntegerField()
    views = models.IntegerField()

# Create your models here.
