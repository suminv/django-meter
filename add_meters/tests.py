from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from add_meters.models import AddMeterData, Profile


User = get_user_model()


class MeterAppTests(TestCase):
    def setUp(self):
        self.password = 'test-pass-123'
        self.user = User.objects.create_user(username='tester', password=self.password)

    def login(self):
        self.client.login(username=self.user.username, password=self.password)

    @staticmethod
    def create_meter_record(user, meter_values, days_ago):
        record = AddMeterData.objects.create(user=user, **meter_values)
        dt = timezone.now() - timedelta(days=days_ago)
        AddMeterData.objects.filter(pk=record.pk).update(created=dt, updated=dt)
        return AddMeterData.objects.get(pk=record.pk)

    def test_add_view_requires_authentication(self):
        response = self.client.get(reverse('meters:create'))
        self.assertEqual(response.status_code, 302)

    def test_logout_post_redirects_to_login(self):
        self.login()
        response = self.client.post(reverse('meters:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('meters:login'))

    def test_add_meter_saves_data_and_shows_success_message(self):
        self.login()
        payload = {
            'meter_1': 100,
            'meter_2': 200,
            'meter_3': 300,
            'meter_4': 400,
            'meter_5': 500,
        }
        response = self.client.post(reverse('meters:create'), data=payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AddMeterData.objects.filter(user=self.user).count(), 1)
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Record added successfully.', messages)

    def test_add_meter_rejects_lower_values_than_previous_record(self):
        self.login()
        self.create_meter_record(
            user=self.user,
            meter_values={
                'meter_1': 100,
                'meter_2': 100,
                'meter_3': 100,
                'meter_4': 100,
                'meter_5': 100,
            },
            days_ago=1,
        )

        response = self.client.post(
            reverse('meters:create'),
            data={
                'meter_1': 90,
                'meter_2': 90,
                'meter_3': 90,
                'meter_4': 90,
                'meter_5': 90,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AddMeterData.objects.filter(user=self.user).count(), 1)
        self.assertContains(response, 'must be greater than or equal to')

    def test_add_meter_rejects_negative_values(self):
        self.login()
        response = self.client.post(
            reverse('meters:create'),
            data={
                'meter_1': -1,
                'meter_2': 10,
                'meter_3': 10,
                'meter_4': 10,
                'meter_5': 10,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AddMeterData.objects.filter(user=self.user).count(), 0)
        self.assertContains(response, 'Value must be zero or positive.')

    def test_profile_create_syncs_user_identity_fields(self):
        self.login()
        payload = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'city': 'Amsterdam',
            'street': 'Main',
            'building': '10A',
            'apartment': 7,
            'phone_number': '+1234567',
        }
        response = self.client.post(reverse('meters:create_profile'), data=payload)
        self.assertEqual(response.status_code, 302)

        profile = Profile.objects.get(user=self.user)
        self.user.refresh_from_db()
        self.assertEqual(profile.email, 'john@example.com')
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')
        self.assertEqual(self.user.email, 'john@example.com')

    def test_profile_edit_updates_profile_and_user_identity_fields(self):
        self.login()
        Profile.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            city='A',
            street='B',
            building='1',
            apartment=1,
            phone_number='111',
        )

        response = self.client.post(
            reverse('meters:update_profile'),
            data={
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane@example.com',
                'city': 'Rotterdam',
                'street': 'New Street',
                'building': '22',
                'apartment': 4,
                'phone_number': '+7777',
            },
        )
        self.assertEqual(response.status_code, 302)

        profile = Profile.objects.get(user=self.user)
        self.user.refresh_from_db()
        self.assertEqual(profile.first_name, 'Jane')
        self.assertEqual(profile.last_name, 'Smith')
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Smith')
        self.assertEqual(self.user.email, 'jane@example.com')

    def test_profile_page_contains_recent_records_and_analytics_context(self):
        self.login()
        for day in range(6, -1, -1):
            self.create_meter_record(
                user=self.user,
                meter_values={
                    'meter_1': 100 + (6 - day) * 5,
                    'meter_2': 200 + (6 - day) * 4,
                    'meter_3': 300 + (6 - day) * 3,
                    'meter_4': 400 + (6 - day) * 2,
                    'meter_5': 500 + (6 - day) * 1,
                },
                days_ago=day,
            )

        response = self.client.get(reverse('meters:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['recent_records']), 5)
        self.assertEqual(len(response.context['summary_30']), 5)
        self.assertEqual(len(response.context['diff_rows']), 5)

    def test_update_meter_rejects_values_lower_than_previous_record(self):
        self.login()
        self.create_meter_record(
            user=self.user,
            meter_values={
                'meter_1': 100,
                'meter_2': 100,
                'meter_3': 100,
                'meter_4': 100,
                'meter_5': 100,
            },
            days_ago=2,
        )
        latest = self.create_meter_record(
            user=self.user,
            meter_values={
                'meter_1': 130,
                'meter_2': 130,
                'meter_3': 130,
                'meter_4': 130,
                'meter_5': 130,
            },
            days_ago=1,
        )

        response = self.client.post(
            reverse('meters:update'),
            data={
                'meter_1': 90,
                'meter_2': 90,
                'meter_3': 90,
                'meter_4': 90,
                'meter_5': 90,
            },
        )
        latest.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(latest.meter_1, 130)
        self.assertContains(response, 'must be greater than or equal to')

    def test_detail_page_builds_chart_context_for_period(self):
        self.login()
        for day in range(10, -1, -1):
            self.create_meter_record(
                user=self.user,
                meter_values={
                    'meter_1': 100 + (10 - day) * 2,
                    'meter_2': 200 + (10 - day) * 2,
                    'meter_3': 300 + (10 - day) * 2,
                    'meter_4': 400 + (10 - day) * 2,
                    'meter_5': 500 + (10 - day) * 2,
                },
                days_ago=day,
            )

        response = self.client.get(reverse('meters:detail'), data={'period': '7'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('chart_labels', response.context)
        self.assertIn('chart_meter_1', response.context)
        self.assertEqual(len(response.context['meter_summaries']), 5)
        self.assertEqual(
            len(response.context['chart_labels']),
            len(response.context['chart_meter_1']),
        )
