from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Student
from .forms import StudentForm

class StudentListView(LoginRequiredMixin, ListView):
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    queryset = Student.objects.all()

class StudentDetailView(LoginRequiredMixin, DetailView):
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    queryset = Student.objects.all()

class StudentCreateView(LoginRequiredMixin, CreateView):
    template_name = 'students/student_form.html'
    form_class = StudentForm
    success_url = reverse_lazy('students:list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class StudentUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'students/student_form.html'
    form_class = StudentForm
    success_url = reverse_lazy('students:list')
    queryset = Student.objects.all()

class StudentDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'students/confirm_delete.html'
    success_url = reverse_lazy('students:list')
    queryset = Student.objects.all()