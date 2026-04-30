"""
URL configuration for tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import redirect_view, generate_qr, dashboard_view
import core.views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', core_views.register_view, name='register'),
    
    # Sistema Interno (SaaS)
    path('', dashboard_view, name='dashboard'),
    path('pages/', core_views.PageListView.as_view(), name='page_list'),
    path('pages/new/', core_views.PageCreateView.as_view(), name='page_create'),
    path('campaigns/', core_views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/new/', core_views.CampaignCreateView.as_view(), name='campaign_create'),
    path('persons/', core_views.PersonListView.as_view(), name='person_list'),
    path('persons/new/', core_views.PersonCreateView.as_view(), name='person_create'),
    path('links/', core_views.TrackedLinkListView.as_view(), name='link_list'),
    path('links/new/', core_views.TrackedLinkCreateView.as_view(), name='link_create'),
    
    # Encurtador e QR
    path('go/<str:shortcode>/', redirect_view, name='redirect'),
    path('qr/<str:shortcode>/', generate_qr, name='qr'),

    # API de cliques em tempo real
    path('api/clicks/', core_views.clicks_api, name='clicks_api'),
]
