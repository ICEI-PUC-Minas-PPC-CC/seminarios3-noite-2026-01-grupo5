from django.db import models

class Resource(models.Model):
    CATEGORY_CHOICES = [
        ('estrategia', 'Estratégia'),
        ('video', 'Vídeo'),
        ('livro', 'Livro'),
        ('artigo', 'Artigo'),
        ('ferramenta', 'Ferramenta'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    file_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title