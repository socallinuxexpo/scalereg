from django.contrib import admin

from .models import Attendee
from .models import Item
from .models import Order
from .models import PromoCode
from .models import Ticket


class AttendeeAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Attendee Info', {
            'fields': ('salutation', 'first_name', 'last_name', 'title', 'org')
        }),
        ('Contact Info', {
            'fields': ('email', 'zip_code', 'phone')
        }),
        ('Badge Info', {
            'fields': ('badge_type', 'valid', 'checked_in')
        }),
        ('Items', {
            'fields': ('ordered_items', 'obtained_items')
        }),
        ('Misc', {
            'fields': ('promo', 'order', 'answers')
        }),
    )
    list_display = ('id', 'first_name', 'last_name', 'email', 'zip_code',
                    'badge_type', 'valid', 'checked_in', 'order', 'promo')
    list_filter = ('badge_type', 'valid', 'checked_in', 'promo',
                   'ordered_items')
    save_on_top = True


class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price', 'active', 'promo',
                    'ticket_offset')
    list_filter = ('active', 'promo', 'ticket_offset')
    save_on_top = True


class OrderAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Billing Info', {
            'fields':
            ('name', 'address', 'city', 'state', 'zip_code', 'country')
        }),
        ('Contact Info', {
            'fields': ('email', 'phone')
        }),
        ('Order Info', {
            'fields': ('order_num', 'valid')
        }),
        ('Payment Info', {
            'fields': ('amount', 'payment_type', 'auth_code', 'pnref',
                       'resp_msg', 'result', 'already_paid_attendees')
        }),
    )
    list_display = ('order_num', 'date', 'name', 'address', 'city', 'state',
                    'zip_code', 'country', 'email', 'phone', 'amount',
                    'payment_type', 'valid')
    list_filter = ('date', 'payment_type', 'valid')
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


admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Ticket, TicketAdmin)
