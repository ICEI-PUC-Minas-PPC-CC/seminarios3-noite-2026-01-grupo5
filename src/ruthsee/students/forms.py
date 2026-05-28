from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'birth_date', 'guardian_name', 'observations']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo do aluno'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do pai, mãe ou responsável'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Estratégias de acalmar ou notas importantes'}),
        }