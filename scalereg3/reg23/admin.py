from django.contrib import admin

from .models import Item
from .models import PromoCode
from .models import Ticket


class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'active', 'promo',
                    'ticket_offset')
    list_filter = ('active', 'promo', 'ticket_offset')
    save_on_top = True


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price_modifier', 'active',
                    'start_date', 'end_date')
    list_filter = ('active', 'start_date', 'end_date')
    save_on_top = True


class TicketAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'ticket_type', 'price', 'public',
                    'cash', 'upgradable', 'start_date', 'end_date')
    list_filter = ('ticket_type', 'public', 'start_date', 'end_date')
    save_on_top = True


admin.site.register(Item, ItemAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Ticket, TicketAdmin)
