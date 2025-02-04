from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView
from . import views

app_name = 'attendance'  # アプリケーションの名前空間を設定

urlpatterns = [
    path('', views.AttendanceListView.as_view(), name='attendance_list'),
    path('create/', views.AttendanceCreateView.as_view(), name='attendance_create'),
    path('create_list/', views.AttendanceCreateListView.as_view(), name='attendance_create_list'),
    path('salary/', views.SalaryListView.as_view(), name='salary_list'),
    path('create_user/', views.UserCreateView.as_view(), name='create_user'),
    path('login/', LoginView.as_view(template_name='attendance/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(template_name='attendance/logout.html', next_page='attendance:login'), name='logout'),
    path('update/<int:pk>/', views.AttendanceUpdateView.as_view(), name='attendance_update'),
    path('update_user/', views.UserUpdateView.as_view(), name='update_user'),
    path('password_change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
]