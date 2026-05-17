from django.db import models

# Modelo para o cadastro de Alunos
class Aluno(models.Model):
    nome = models.CharField(max_length=100)
    ra = models.CharField(max_length=20, unique=True)
    turma = models.CharField(max_length=50)
    foto = models.ImageField(upload_to='alunos/', blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

# Modelo para os Vídeos Complementares
class VideoComplementar(models.Model):
    CATEGORIAS = [
        ('manejo', 'Manejo Comportamental'),
        ('pedagogico', 'Apoio Pedagógico'),
        ('atividades', 'Sugestões de Atividades'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título do Vídeo")
    youtube_id = models.CharField(max_length=20, verbose_name="ID do Vídeo (ex: dQw4w9WgXcQ)")
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, verbose_name="Categoria")
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.get_categoria_display()}"
    
class Comunicado(models.Model):
    titulo = models.CharField(max_length=200)
    texto = models.TextField()
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    def is_ativo(self):
        from django.utils import timezone
        agora = timezone.now()
        return self.ativo and self.data_inicio <= agora <= self.data_fim