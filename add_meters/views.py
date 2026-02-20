from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib import messages
from collections import defaultdict
from datetime import timedelta
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, UpdateView, TemplateView, FormView, CreateView
from django.utils import timezone

from .forms import AddMeterForm, AddMeterUpdateForm
from .models import AddMeterData, Profile


def sync_user_identity_from_profile(user, profile):
    user.first_name = profile.first_name
    user.last_name = profile.last_name
    user.email = profile.email
    user.save(update_fields=['first_name', 'last_name', 'email'])


class StartPageView(TemplateView):
    template_name = 'add_meters/index.html'


class ProfileListView(LoginRequiredMixin, TemplateView):
    template_name = 'add_meters/profile.html'
    meter_keys = ['meter_1', 'meter_2', 'meter_3', 'meter_4', 'meter_5']
    meter_labels = {
        'meter_1': 'Meter 1',
        'meter_2': 'Meter 2',
        'meter_3': 'Meter 3',
        'meter_4': 'Meter 4',
        'meter_5': 'Meter 5',
    }

    @staticmethod
    def _get_range_days(records):
        if not records:
            return 1
        return max(1, (records[-1].created.date() - records[0].created.date()).days + 1)

    def _get_last_and_prev_records(self):
        records = AddMeterData.objects.filter(user=self.request.user).order_by('-created')[:2]
        last_record = records[0] if len(records) > 0 else None
        prev_record = records[1] if len(records) > 1 else None
        return last_record, prev_record

    def _get_30_day_consumption_totals(self):
        records_30 = list(
            AddMeterData.objects.filter(
                user=self.request.user,
                created__gte=timezone.now() - timedelta(days=30),
            ).order_by('created')
        )
        totals_30 = {key: 0 for key in self.meter_keys}

        if len(records_30) > 1:
            prev_item = records_30[0]
            for item in records_30[1:]:
                for key in self.meter_keys:
                    totals_30[key] += getattr(item, key) - getattr(prev_item, key)
                prev_item = item

        return totals_30, self._get_range_days(records_30)

    def _build_30_day_summary(self, totals_30, range_days_30):
        return [
            {
                'label': self.meter_labels[key],
                'total': totals_30[key],
                'avg_per_day': round(totals_30[key] / range_days_30, 2),
            }
            for key in self.meter_keys
        ]

    def _build_diff_rows(self, diffs, totals_30, range_days_30):
        rows = []
        for key in self.meter_keys:
            avg = round(totals_30[key] / range_days_30, 2) if range_days_30 else 0
            diff = diffs[key]
            if diff < 0:
                status_label = 'Decrease'
                status_class = 'danger'
            elif avg > 0 and diff > avg * 1.5:
                status_label = 'High spike'
                status_class = 'warning'
            elif avg > 0 and diff < avg * 0.7:
                status_label = 'Low usage'
                status_class = 'info'
            else:
                status_label = 'Normal'
                status_class = 'success'

            rows.append({
                'label': self.meter_labels[key],
                'value': diff,
                'status_label': status_label,
                'status_class': status_class,
            })
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['profile'] = Profile.objects.filter(user=self.request.user).first()
        context['recent_records'] = AddMeterData.objects.filter(user=self.request.user).order_by('-created')[:5]
        last_record, prev_record = self._get_last_and_prev_records()
        context['last_record'] = last_record
        context['prev_record'] = prev_record

        totals_30, range_days_30 = self._get_30_day_consumption_totals()
        context['summary_30'] = self._build_30_day_summary(totals_30, range_days_30)

        if last_record and prev_record:
            date_now = timezone.localtime()
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

            diffs = {
                'meter_1': diff_meter_1,
                'meter_2': diff_meter_2,
                'meter_3': diff_meter_3,
                'meter_4': diff_meter_4,
                'meter_5': diff_meter_5,
            }
            context['diff_rows'] = self._build_diff_rows(diffs, totals_30, range_days_30)

        return context


class MeterFormView(LoginRequiredMixin, View):
    @staticmethod
    def get_last_record_for_user(user):
        return AddMeterData.objects.filter(user=user).order_by('-created').first()

    def get(self, request):
        form = AddMeterForm(user=request.user)
        context = {
            'form': form,
            'last_record': self.get_last_record_for_user(request.user),
        }
        return render(request, 'add_meters/create.html', context)

    def post(self, request):
        form = AddMeterForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save(commit=False)
            form.instance.user = request.user
            form.save()
            messages.success(request, 'Record added successfully.')
            return redirect('meters:profile')
        else:
            context = {
                'form': form,
                'last_record': self.get_last_record_for_user(request.user),
            }
            return render(request, 'add_meters/create.html', context)


class MeterUpdateView(LoginRequiredMixin, UpdateView):
    model = AddMeterData
    form_class = AddMeterUpdateForm
    template_name = 'add_meters/update.html'
    success_url = reverse_lazy('meters:profile')

    def get_object(self, queryset=None):
        """if qs is empty, show error 404"""
        try:
            return AddMeterData.objects.filter(user=self.request.user).latest('created')
        except AddMeterData.DoesNotExist:
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs



class MeterDetailView(LoginRequiredMixin, ListView):
    model = AddMeterData
    template_name = 'add_meters/detail.html'
    context_object_name = 'meters'

    PERIOD_OPTIONS = (
        ('7', 'Last 7 days'),
        ('30', 'Last 30 days'),
        ('90', 'Last 90 days'),
        ('180', 'Last 180 days'),
        ('365', 'Last 365 days'),
        ('all', 'All time'),
    )

    def get_selected_period(self):
        period = self.request.GET.get('period', '30')
        allowed = {value for value, _ in self.PERIOD_OPTIONS}
        return period if period in allowed else '30'

    def get_bucket_type(self):
        period = self.get_selected_period()
        if period == 'all':
            return 'month'
        days = int(period)
        if days <= 30:
            return 'day'
        if days <= 180:
            return 'week'
        return 'month'

    def get_queryset(self):
        qs = AddMeterData.objects.filter(user=self.request.user)
        period = self.get_selected_period()
        if period != 'all':
            days = int(period)
            start = timezone.now() - timedelta(days=days)
            qs = qs.filter(created__gte=start)
        return qs.order_by('-created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['period_options'] = self.PERIOD_OPTIONS
        context['selected_period'] = self.get_selected_period()

        chart_qs = list(self.object_list.order_by('created'))
        meter_keys = ['meter_1', 'meter_2', 'meter_3', 'meter_4', 'meter_5']
        meter_labels = {
            'meter_1': 'Meter 1',
            'meter_2': 'Meter 2',
            'meter_3': 'Meter 3',
            'meter_4': 'Meter 4',
            'meter_5': 'Meter 5',
        }

        bucket_type = self.get_bucket_type()
        bucket_order = []
        bucket_values = defaultdict(lambda: {key: 0 for key in meter_keys})

        prev_record = None
        for item in chart_qs:
            if prev_record is None:
                prev_record = item
                continue

            if bucket_type == 'day':
                bucket_key = item.created.strftime('%d.%m.%Y')
            elif bucket_type == 'week':
                iso_year, iso_week, _ = item.created.isocalendar()
                bucket_key = f'W{iso_week:02d} {iso_year}'
            else:
                bucket_key = item.created.strftime('%m.%Y')

            if bucket_key not in bucket_values:
                bucket_order.append(bucket_key)

            for key in meter_keys:
                bucket_values[bucket_key][key] += getattr(item, key) - getattr(prev_record, key)

            prev_record = item

        context['chart_labels'] = bucket_order
        context['chart_meter_1'] = [bucket_values[label]['meter_1'] for label in bucket_order]
        context['chart_meter_2'] = [bucket_values[label]['meter_2'] for label in bucket_order]
        context['chart_meter_3'] = [bucket_values[label]['meter_3'] for label in bucket_order]
        context['chart_meter_4'] = [bucket_values[label]['meter_4'] for label in bucket_order]
        context['chart_meter_5'] = [bucket_values[label]['meter_5'] for label in bucket_order]
        context['chart_title'] = 'Consumption by period'

        summaries = []
        range_days = 0
        if chart_qs:
            first_day = chart_qs[0].created.date()
            last_day = chart_qs[-1].created.date()
            range_days = max(1, (last_day - first_day).days + 1)

        for key in meter_keys:
            total = sum(bucket_values[label][key] for label in bucket_order)
            trend = 0
            if len(bucket_order) >= 2:
                trend = bucket_values[bucket_order[-1]][key] - bucket_values[bucket_order[-2]][key]
            avg_per_day = round(total / range_days, 2) if range_days else 0
            summaries.append({
                'label': meter_labels[key],
                'total': total,
                'trend': trend,
                'avg_per_day': avg_per_day,
            })
        context['meter_summaries'] = summaries

        return context


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

    def get_success_url(self):
        """The get user.id param in url"""
        if self.request.user.is_authenticated:
            return reverse_lazy('meters:create_profile')
        else:
            return reverse_lazy('meters:login')


    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('meters:profile')
        return super(RegisterPage, self).get(*args, **kwargs)



class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Profile
    fields = ('first_name', 'last_name', 'city', 'street', 'building', 'apartment', 'phone_number', 'email')
    template_name = 'add_meters/profile_update.html'
    success_url = reverse_lazy('meters:profile')

    def dispatch(self, request, *args, **kwargs):
        if Profile.objects.filter(user=request.user).exists():
            return redirect('meters:profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        sync_user_identity_from_profile(self.request.user, form.instance)
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ('first_name', 'last_name', 'city', 'street', 'building', 'apartment', 'phone_number', 'email')
    template_name = 'add_meters/profile_update.html'
    success_url = reverse_lazy('meters:profile')

    def dispatch(self, request, *args, **kwargs):
        if not Profile.objects.filter(user=request.user).exists():
            return redirect('meters:create_profile')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def form_valid(self, form):
        sync_user_identity_from_profile(self.request.user, form.instance)
        return super().form_valid(form)
