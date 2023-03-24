from django import forms

from add_meters.models import AddMeterData


class AddMeterForm(forms.ModelForm):
    class Meta:
        model = AddMeterData
        fields = ('meter_1', 'meter_2', 'meter_3', 'meter_4', 'meter_5')

    def __init__(self, user, *args, **kwargs):
        # for transfer user to clean
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        # Check that new meter data is greater than previous data
        cleaned_data = super().clean()

        prev_data = AddMeterData.objects.filter(user=self.user).order_by('-created').first()
        if prev_data:
            for i in range(1, 6):
                prev_meter = getattr(prev_data, f'meter_{i}')
                new_meter = cleaned_data.get(f'meter_{i}')
                # allow the user to submit the same meter reading as the previous reading
                # if new_meter is not None and new_meter < prev_meter:
                if new_meter < prev_meter:
                    raise forms.ValidationError(f'Meter {i} must be greater than {prev_meter} previous reading. ')

        return cleaned_data

