from django.contrib.auth.models import User
from django.db import models


class AddMeterData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meter_1 = models.IntegerField()
    meter_2 = models.IntegerField()
    meter_3 = models.IntegerField()
    meter_4 = models.IntegerField()
    meter_5 = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'User: {self.user.last_name}, Date: {self.created}'


# TODO Make new model Profile.
