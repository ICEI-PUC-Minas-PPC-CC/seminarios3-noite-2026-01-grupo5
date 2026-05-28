from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'student', 'relationship', 'phone', 'is_emergency')
    list_filter = ('relationship', 'is_emergency', 'created_at')
    search_fields = ('name', 'student__name', 'phone')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Relacionamento', {
            'fields': ('student', 'relationship', 'is_emergency')
        }),
        ('Auditoria', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )