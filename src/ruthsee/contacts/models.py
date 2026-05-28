from django.db import models
from students.models import Student

class Contact(models.Model):
    RELATIONSHIP_CHOICES = [
        ('pai', 'Pai'),
        ('mae', 'Mãe'),
        ('tutor', 'Tutor/Guardião'),
        ('outro', 'Outro'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, default='outro')
    is_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"

    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()}) - {self.student.name}"