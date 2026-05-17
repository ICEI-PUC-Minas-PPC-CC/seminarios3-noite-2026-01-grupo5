from django.contrib import admin
from .models import Aluno, VideoComplementar

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ra', 'turma')
    search_fields = ('nome', 'ra')

@admin.register(VideoComplementar)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'data_criacao')
    list_filter = ('categoria',)

@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'data_inicio', 'data_fim', 'ativo', 'is_ativo')
    list_filter = ('ativo', 'data_inicio')
    list_editable = ('ativo',)