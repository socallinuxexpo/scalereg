from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Answer
from .models import Attendee
from .models import Item
from .models import Order
from .models import PaymentCode
from .models import PromoCode
from .models import Question
from .models import Ticket
from .models import Upgrade


def link_to_badge_type(ticket):
    url = reverse('admin:reg23_ticket_change', args=[ticket.name])
    return format_html('<a href="{}">{}</a>', url, ticket.name)


def link_to_order(order):
    if not order:
        return '-'
    url = reverse('admin:reg23_order_change', args=[order.order_num])
    return format_html('<a href="{}">{}</a>', url, order.order_num)


def link_to_promo(promo):
    if not promo:
        return '-'
    url = reverse('admin:reg23_promocode_change', args=[promo.name])
    return format_html('<a href="{}">{}</a>', url, promo.name)


class ListAnswerInline(admin.TabularInline):
    extra = 3
    model = Answer
    verbose_name = 'List Answer'


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text')
    save_on_top = True


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
        ('Misc', {
            'fields': ('promo', 'order', 'ordered_items', 'answers')
        }),
    )
    list_display = ('id', 'first_name', 'last_name', 'email', 'zip_code',
                    'link_to_badge_type', 'valid', 'checked_in',
                    'link_to_order', 'link_to_promo')
    list_filter = ('badge_type', 'valid', 'checked_in', 'promo',
                   'ordered_items')
    list_select_related = ('badge_type', 'order', 'promo')
    save_on_top = True

    def link_to_badge_type(self, obj):
        return link_to_badge_type(obj.badge_type)

    def link_to_order(self, obj):
        return link_to_order(obj.order)

    def link_to_promo(self, obj):
        return link_to_promo(obj.promo)


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
            'fields':
            ('amount', 'payment_type', 'payflow_auth_code', 'payflow_pnref',
             'payflow_resp_msg', 'payflow_result', 'already_paid_attendees')
        }),
    )
    list_display = ('order_num', 'date', 'name', 'address', 'city', 'state',
                    'zip_code', 'country', 'email', 'phone', 'amount',
                    'payment_type', 'valid')
    list_filter = ('date', 'payment_type', 'valid')
    save_on_top = True


class PaymentCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'link_to_badge_type', 'link_to_order',
                    'max_attendees')
    list_filter = ('code', 'badge_type')
    list_select_related = ('badge_type', 'order')
    save_on_top = True

    def link_to_badge_type(self, obj):
        return link_to_badge_type(obj.badge_type)

    def link_to_order(self, obj):
        return link_to_order(obj.order)


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'price_modifier', 'active',
                    'start_date', 'end_date')
    list_filter = ('active', 'start_date', 'end_date')
    save_on_top = True


class QuestionAdmin(admin.ModelAdmin):
    inlines = []
    model = Question
    save_on_top = True

    def get_inlines(self, request, obj):
        if obj and obj.is_text_question:
            return []
        return [ListAnswerInline]


class TicketAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'ticket_type', 'price', 'public',
                    'cash', 'upgradable', 'start_date', 'end_date')
    list_filter = ('ticket_type', 'public', 'start_date', 'end_date')
    save_on_top = True


class UpgradeAdmin(admin.ModelAdmin):
    list_display = ('valid', 'attendee', 'link_to_old_badge_type',
                    'link_to_new_badge_type', 'link_to_old_order',
                    'link_to_new_order')
    list_filter = ['valid']
    list_select_related = ('old_badge_type', 'new_badge_type', 'old_order',
                           'new_order')
    save_on_top = True

    def link_to_new_badge_type(self, obj):
        return link_to_badge_type(obj.new_badge_type)

    def link_to_new_order(self, obj):
        return link_to_order(obj.new_order)

    def link_to_old_badge_type(self, obj):
        return link_to_badge_type(obj.old_badge_type)

    def link_to_old_order(self, obj):
        return link_to_order(obj.old_order)


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PaymentCode, PaymentCodeAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Upgrade, UpgradeAdmin)
