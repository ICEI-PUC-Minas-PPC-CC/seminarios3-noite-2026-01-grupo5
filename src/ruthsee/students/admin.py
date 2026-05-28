from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'guardian_name', 'birth_date')
    search_fields = ('name', 'guardian_name')