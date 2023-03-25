from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, UpdateView, DetailView, TemplateView, FormView
from datetime import datetime
import pytz

from .forms import AddMeterForm
from .models import AddMeterData



class StartPageView(TemplateView):
    template_name = 'add_meters/index.html'


class ProfileListView(ListView):
    model = AddMeterData
    template_name = 'add_meters/profile.html'
    context_object_name = 'qs'

    def get_queryset(self):
        """show data for current login user"""
        qs_last = AddMeterData.objects.filter(user=self.request.user).order_by('-created')[:1]
        qs_prev = AddMeterData.objects.filter(user=self.request.user).order_by('-created')[1:2]
        return list(qs_last) + list(qs_prev)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the last two records in the database
        records = AddMeterData.objects.filter(user=self.request.user).order_by('-created')[:2]
        # If there are at least two records, calculate the difference
        if len(records) == 2:
            last_record = records[0]
            prev_record = records[1]
            date_now = datetime.now(tz=pytz.timezone("Europe/Amsterdam"))
            diff_meter_1 = last_record.meter_1 - prev_record.meter_1
            diff_meter_2 = last_record.meter_2 - prev_record.meter_2
            diff_meter_3 = last_record.meter_3 - prev_record.meter_3
            diff_meter_4 = last_record.meter_4 - prev_record.meter_4
            diff_meter_5 = last_record.meter_5 - prev_record.meter_5
            context['diff_meter_1'] = diff_meter_1
            context['diff_meter_2'] = diff_meter_2
            context['diff_meter_3'] = diff_meter_3
            context['diff_meter_4'] = diff_meter_4
            context['diff_meter_5'] = diff_meter_5
            context['date_now'] = date_now

        return context


class MeterFormView(View):

    def get(self, request):
        form = AddMeterForm(user=request.user)
        return render(request, 'add_meters/create.html', {'form': form})

    def post(self, request):
        form = AddMeterForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save(commit=False)
            form.instance.user = request.user
            form.save()
            return redirect('meters:profile')
        else:
            return render(request, 'add_meters/create.html', {'form': form})


class MeterUpdateView(UpdateView):
    model = AddMeterData
    fields = ['meter_1', 'meter_2', 'meter_3', 'meter_4', 'meter_5']
    template_name = 'add_meters/update.html'
    success_url = reverse_lazy('meters:profile')

    def get_object(self, queryset=None):
        try:
            obj = AddMeterData.objects.filter(user=self.request.user).latest('created')
            return obj
        except AddMeterData.DoesNotExist:
            raise Http404('Meter data not found')
        except ValueError:
            raise Http404('Invalid meter data id')


class MeterDetailView(DetailView):
    model = AddMeterData
    template_name = 'add_meters/detail.html'

    def get_object(self, queryset=None):
        return AddMeterData.objects.filter(user=self.request.user).order_by('-created')


class UserLoginView(LoginView):
    template_name = 'add_meters/login.html'
    fields = '__all___'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('meters:profile')



class RegisterPage(FormView):
    template_name = 'add_meters/register.html'
    form_class = UserCreationForm

    redirect_authenticated_user = True
    success_url = reverse_lazy('meters:profile')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('meters:profile')
        return super(RegisterPage, self).get(*args, **kwargs)