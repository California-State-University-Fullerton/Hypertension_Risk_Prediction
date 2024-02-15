from django.db import models

GENDER_CHOICES = {
    ('0', 'female'),      
    ('1', 'male')
                }

# Create your models here.
class Patient(models.Model):
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=1)
    age = models.PositiveSmallIntegerField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fname} id:{self.id}"
