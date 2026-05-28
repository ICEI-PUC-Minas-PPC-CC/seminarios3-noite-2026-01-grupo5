from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Resource
from .forms import ResourceForm

class ResourceListView(LoginRequiredMixin, ListView):
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'

class ResourceDetailView(LoginRequiredMixin, DetailView):
    model = Resource
    template_name = 'resources/resource_detail.html'
    context_object_name = 'resource'

class ResourceCreateView(LoginRequiredMixin, CreateView):
    model = Resource
    form_class = ResourceForm
    template_name = 'resources/resource_form.html'
    success_url = reverse_lazy('resources:list')

class ResourceUpdateView(LoginRequiredMixin, UpdateView):
    model = Resource
    form_class = ResourceForm
    template_name = 'resources/resource_form.html'
    success_url = reverse_lazy('resources:list')

class ResourceDeleteView(LoginRequiredMixin, DeleteView):
    model = Resource
    template_name = 'resources/resource_confirm_delete.html'
    success_url = reverse_lazy('resources:list')