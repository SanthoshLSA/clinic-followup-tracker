from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('followup/create/', views.create_followup, name='create_followup'),
    path('followup/<int:pk>/edit/', views.edit_followup, name='edit_followup'),
    path('followup/<int:pk>/mark-done/', views.mark_done, name='mark_done'),
    path('p/<str:token>/', views.public_view, name='public_view'),
]