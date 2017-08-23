from django.db import models

class Requirement(models.Model):
    email = models.EmailField()
    content = models.TextField(default='')
