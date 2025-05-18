from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from catalogs.models import Device


class DeviceListView(LoginRequiredMixin, ListView):
    model = Device
    template_name = 'device_list.html'
    context_object_name = 'devices'
    ordering = ['category', 'type', 'manufacturer', 'model']


class DeviceCreateView(LoginRequiredMixin, CreateView):
    model = Device
    template_name = 'device_form.html'
    fields = ['category', 'type', 'manufacturer', 'model', 'notes']
    success_url = reverse_lazy('devices:device-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Устройство "{self.object}" было успешно создано.')
        return response


class DeviceUpdateView(LoginRequiredMixin, UpdateView):
    model = Device
    template_name = 'device_form.html'
    fields = ['category', 'type', 'manufacturer', 'model', 'notes']
    success_url = reverse_lazy('devices:device-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Устройство "{self.object}" было успешно изменено.')
        return response


class DeviceDeleteView(LoginRequiredMixin, DeleteView):
    model = Device
    template_name = 'device_confirm_delete.html'
    success_url = reverse_lazy('devices:device-list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Устройство "{obj}" было успешно удалено.')
        return response 