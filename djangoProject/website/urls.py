from django.urls import path

from website.views import HomeView, DetailView, CartView, OrderView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('detail/<int:game_id>/', DetailView.as_view(), name='detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('order/', OrderView.as_view(), name='order'),
]
