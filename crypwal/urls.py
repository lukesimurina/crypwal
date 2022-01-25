from django.urls import path
from crypwal.views import addWalletView, deleteWalletView

from . import views

urlpatterns = [
    path('', views.index, name='home'),
     path('addWalletItem/',addWalletView), 
     path('deleteWalletItem/<int:i>/', deleteWalletView), 
]