from django.contrib import admin
from .models import Item
from .models import Order
from .models import Package
from .models import PromoCode
from .models import Sponsor


class PromoCodeAdmin(admin.ModelAdmin):
  list_display = ('name', 'description', 'price_modifier', 'active',
                  'start_date', 'end_date')
  list_filter = ('active', 'start_date', 'end_date')
  save_on_top = True


class ItemAdmin(admin.ModelAdmin):
  list_display = ('name', 'description', 'long_description', 'price', 'active',
                  'promo', 'package_offset')
  list_filter = ('active', 'promo', 'package_offset')
  save_on_top = True


class OrderAdmin(admin.ModelAdmin):
  fieldsets = (
    ('Billing Info', {'fields': ('name', 'address', 'city', 'state', 'zip_code',
                                 'country')}),
    ('Contact Info', {'fields': ('email', 'phone')}),
    ('Order Info', {'fields': ('order_num', 'valid')}),
    ('Payment Info', {'fields': ('amount', 'auth_code', 'pnref', 'resp_msg',
                                 'result')}),
  )
  list_display = ('order_num', 'date', 'name', 'address', 'city', 'state',
                  'zip_code', 'country', 'email', 'phone', 'amount', 'valid')
  list_filter = ('date', 'valid')
  save_on_top = True


class SponsorAdmin(admin.ModelAdmin):
  fieldsets = (
    ('Sponsor Info', {'fields': ('salutation', 'first_name', 'last_name',
                                 'title', 'org')}),
    ('Contact Info', {'fields': ('email', 'zip_code', 'phone')}),
    ('Misc', {'fields': ('package', 'promo', 'valid', 'ordered_items')}),
  )
  list_display = ('id', 'first_name', 'last_name', 'email', 'zip_code', 'valid',
                  'order', 'package', 'promo')
  list_filter = ('valid', 'package', 'promo', 'ordered_items')
  save_on_top = True


class PackageAdmin(admin.ModelAdmin):
  list_display = ('name', 'description', 'long_description', 'price', 'public',
                  'start_date', 'end_date')
  list_filter = ('public', 'start_date', 'end_date')
  save_on_top = True


admin.site.register(Item, ItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Sponsor, SponsorAdmin)
