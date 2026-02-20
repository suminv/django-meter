
from django.urls import path
from django.contrib.auth.views import LogoutView

from add_meters.views import ProfileListView, MeterFormView, MeterUpdateView, MeterDetailView, StartPageView, \
    UserLoginView, RegisterPage, ProfileCreateView, ProfileUpdateView

app_name = 'meters'


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='meters:login'), name='logout'),
    path('register/', RegisterPage.as_view(), name='register'),
    path('', StartPageView.as_view(), name='start-page'),
    path('profile/', ProfileListView.as_view(), name='profile'),
    path('add/', MeterFormView.as_view(), name='create'),
    path('update/', MeterUpdateView.as_view(), name='update'),
    path('detail/', MeterDetailView.as_view(), name='detail'),
    path('create_profile/', ProfileCreateView.as_view(), name='create_profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='update_profile'),








]
