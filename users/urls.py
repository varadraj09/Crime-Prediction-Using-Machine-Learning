from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from users import views

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', views.index, name='index'),
    path('index/', views.index, name='index'),

    path('AdminLogin/', views.AdminLogin, name='AdminLogin'),
    path('UserLogin/', views.UserLogin, name='UserLogin'),
    path('UserRegister/', views.UserRegister, name='UserRegister'),

    path('AdminHome/', views.AdminHome, name='AdminHome'),
    path('AdminLoginCheck/', views.AdminLoginCheck, name='AdminLoginCheck'),

    path('RegisterUsersView/', views.RegisterUsersView, name='RegisterUsersView'),

    path('ActivaUsers/', views.ActivaUsers, name='ActivaUsers'),

    path('UserRegisterActions/', views.UserRegisterActions, name='UserRegisterActions'),

    path('UserLoginCheck/', views.UserLoginCheck, name='UserLoginCheck'),

    path('UserHome/', views.UserHome, name='UserHome'),

    path('viewData', views.viewData, name='viewData'),

    path('AddCrime/', views.add_crime, name='add_Crime'),
   
    path('area_analysis/', views.area_analysis, name='area_analysis'),

path('route_safety/', views.route_safety, name='route_safety'),

path('map_view/', views.map_view, name='map_view'),

path('insights/', views.insights, name='insights'),

path('chatbot/', views.chatbot, name='chatbot'),

path('emergency/', views.emergency, name='emergency'),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

