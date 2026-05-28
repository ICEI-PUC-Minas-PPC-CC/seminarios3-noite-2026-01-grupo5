from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    birth_date = models.DateField()
    guardian_name = models.CharField(max_length=100)
    observations = models.TextField(blank=True, null=True, help_text="Estratégias de acalmar")

    def __str__(self):
        return self.name