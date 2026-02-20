from django import forms

from add_meters.models import AddMeterData


class BaseMeterForm(forms.ModelForm):
    meter_fields = ('meter_1', 'meter_2', 'meter_3', 'meter_4', 'meter_5')

    def __init__(self, user=None, *args, **kwargs):
        # Keep explicit user for validation and fallback to instance user in update flow.
        self.user = user or getattr(kwargs.get('instance'), 'user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        for field_name in self.meter_fields:
            value = cleaned_data.get(field_name)
            if value is not None and value < 0:
                errors[field_name] = 'Value must be zero or positive.'

        if self.user:
            prev_qs = AddMeterData.objects.filter(user=self.user).order_by('-created')
            if self.instance and self.instance.pk:
                prev_qs = prev_qs.exclude(pk=self.instance.pk)
            prev_data = prev_qs.first()

            if prev_data:
                for i in range(1, 6):
                    field_name = f'meter_{i}'
                    prev_meter = getattr(prev_data, field_name)
                    new_meter = cleaned_data.get(field_name)
                    if new_meter is not None and new_meter < prev_meter:
                        errors[field_name] = f'Meter {i} must be greater than or equal to {prev_meter}.'

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data


class AddMeterForm(BaseMeterForm):
    class Meta:
        model = AddMeterData
        fields = ('meter_1', 'meter_2', 'meter_3', 'meter_4', 'meter_5')


class AddMeterUpdateForm(BaseMeterForm):
    class Meta:
        model = AddMeterData
        fields = ('meter_1', 'meter_2', 'meter_3', 'meter_4', 'meter_5')
