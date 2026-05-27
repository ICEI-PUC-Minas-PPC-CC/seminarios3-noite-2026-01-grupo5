from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from students.models import Student
from resources.models import Resource
from contacts.models import Contact

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'
    login_url = reverse_lazy('accounts:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_students'] = Student.objects.count()
        context['total_resources'] = Resource.objects.count()
        context['total_contacts'] = Contact.objects.count()
        context['emergency_contacts'] = Contact.objects.filter(is_emergency=True).count()
        return context