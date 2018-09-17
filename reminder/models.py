from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.
class Reminder(models.Model):

    ####Seems been depriciated####
    # ALWAYS = 0
    # RAIN = 1
    # SNOW = 2
    # TEMPDROP3F = 3
    # TEMPRISE3F = 4
    # MAX_CHOICES = 5
    # WARNING_TEXT = [
    #     'Always',
    #     'Raining tomorrow',
    #     'Snowing tomorrow',
    #     'Temperature dropping by 3F tomorrow',
    #     'Temperature rising by 3F tomorrow',
    # ]
    # WARNING_CHOICE = [(i, WARNING_TEXT[i]) for i in range(MAX_CHOICES)]

    WARNING_CHOICE = (
        (1, 'Always'),
        (2,'Raining tomorrow'),
        (3,'Snowing tomorrow'),
        (4,'Temperature dropping by 10F tomorrow'),
        (5,'Temperature rising by 10F tomorrow'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)#models.DO_NOTHING
    zipcode = models.CharField(max_length=30)
    warning_event = models.IntegerField(default=1, choices=WARNING_CHOICE)
    reminder_sent = models.DateField(default=datetime.min, blank=True)

    def __str__(self):
        return self.user.get_username() + '_' + self.zipcode


class ReminderTime(models.Model):
    Time_CHOICE = (
        (1, '10:00 pm CDT every night'),
        (2, '6:00 am CDT every morning'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE,primary_key=True)  # models.DO_NOTHING
    reminder_time = models.IntegerField(default=1, choices=Time_CHOICE)

    def __str__(self):
        return self.user.get_username() + '_' + str(self.get_reminder_time_display())

class Weather(models.Model):
    zipcode = models.CharField(max_length=30, null=False)
    time = models.DateField(default=datetime.min, blank=True, null=False)
    description = models.CharField(max_length=50)
    weather_sign = models.IntegerField(default=0)
    city = models.CharField(max_length=30)
    temp_min = models.CharField(max_length=10)
    temp_max = models.CharField(max_length=10)


    class Meta:
        unique_together = ('zipcode', 'time')
