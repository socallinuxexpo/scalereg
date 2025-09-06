from django.contrib import admin

from .models import Item
from .models import Package
from .models import PromoCode


class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'long_description', 'price',
                    'active', 'promo', 'package_offset')
    list_filter = ('active', 'promo', 'package_offset')
    save_on_top = True


class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'long_description', 'price',
                    'public', 'start_date', 'end_date')
    list_filter = ('public', 'start_date', 'end_date')
    save_on_top = True


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price_modifier', 'active',
                    'start_date', 'end_date')
    list_filter = ('active', 'start_date', 'end_date')
    save_on_top = True


admin.site.register(Item, ItemAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
