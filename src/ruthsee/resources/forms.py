from django import forms
from .models import Resource

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do recurso'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descrição detalhada'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'file_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://exemplo.com'}),
        }