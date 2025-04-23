from django.db import models

# Create your models here.
class Department(models.Model):
    title = models.CharField(max_length=100, blank=False)
    phone = models.CharField(max_length=20, blank=False)

class Worker(models.Model):
    name = models.CharField(max_length=20, blank=False)
    second_name = models.CharField(max_length=35, blank=False)
    salary = models.IntegerField(default=0)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
