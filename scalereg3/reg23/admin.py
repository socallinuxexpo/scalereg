from django.contrib import admin

from .models import Answer
from .models import Attendee
from .models import Item
from .models import Order
from .models import PromoCode
from .models import Question
from .models import Ticket


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


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Ticket, TicketAdmin)
