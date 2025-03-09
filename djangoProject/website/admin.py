from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path

from website.forms import ExcelImportForm
from website.models import Game, GameImage, SteamGame, PriceRule, Incoming, Distributor, Developer, Publisher, \
    Concurrent, ConcurrentPrice, Category, Key, Order, OrderItem
from website.tasks import import_incoming


# Register your models here.
@admin.register(Game, SteamGame, GameImage, PriceRule, Distributor, Developer, Publisher, Concurrent, Category,
                OrderItem)
class DefaultAdmin(admin.ModelAdmin):
    pass


@admin.register(Incoming)
class IncomingAdmin(admin.ModelAdmin):
    change_list_template = "admin/incoming_changelist.html"
    list_display = ['distributor__name', 'date', 'game__name']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [path('import-excel/', self.import_csv), ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            excel_file = request.FILES["excel_file"]

            import_incoming.delay(excel_file.read())

            self.message_user(request, "Файл передан в обработку")
            return redirect("..")
        form = ExcelImportForm()
        payload = {"form": form}
        return render(
            request, "admin/excel_form.html", payload
        )


@admin.register(Key)
class KeyAdmin(admin.ModelAdmin):
    search_fields = ['is_sold', 'incoming__game__name', ]
    list_display = ['incoming_id', 'value', 'is_sold', ]


@admin.register(ConcurrentPrice)
class ConcurrentPriceAdmin(admin.ModelAdmin):
    ordering = ['-is_lower_price', 'game']
    search_fields = ['game__name', 'concurrent__name', 'price']
    list_display = [field.name for field in ConcurrentPrice._meta.get_fields()]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    search_fields = ['email', 'date']
    ordering = ['-date', ]
    list_display = ['email', 'date', 'price']
