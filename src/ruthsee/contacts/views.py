from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Contact
from .forms import ContactForm
from django.urls import reverse_lazy

class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'contacts/list.html'
    context_object_name = 'contacts'

class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/form.html'
    success_url = '/contacts/'

class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/form.html'
    success_url = '/contacts/'

class ContactDeleteView(LoginRequiredMixin, DeleteView):
    model = Contact
    success_url = '/contacts/'
    template_name = 'contacts/confirm_delete.html'


class ContactCreateView(CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')


class ContactUpdateView(UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')