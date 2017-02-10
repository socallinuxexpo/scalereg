from django.contrib import admin
from models import Answer
from models import Attendee
from models import Coupon
from models import Item
from models import ListAnswer
from models import ListQuestion
from models import Order
from models import PromoCode
from models import Reprint
from models import TextAnswer
from models import TextQuestion
from models import Ticket
from models import Upgrade


class ReprintAdmin(admin.ModelAdmin):
  save_on_top = True


class ListAnswerInline(admin.TabularInline):
  model = ListAnswer
  extra = 3


class PromoCodeAdmin(admin.ModelAdmin):
  list_display = ('name', 'description', 'price_modifier', 'active',
                  'start_date', 'end_date')
  list_filter = ('active', 'start_date', 'end_date')
  save_on_top = True


class ListQuestionAdmin(admin.ModelAdmin):
  save_on_top = True
  model = ListQuestion
  inlines = [ListAnswerInline]


class TextQuestionAdmin(admin.ModelAdmin):
  save_on_top = True


class ItemAdmin(admin.ModelAdmin):
  list_display = ('name', 'description', 'price', 'active', 'pickup', 'promo',
                  'ticket_offset')
  list_filter = ('active', 'pickup', 'promo', 'ticket_offset')
  save_on_top = True


class ListAnswerAdmin(admin.ModelAdmin):
  list_display = ('question', '__str_text__')
  save_on_top = True


class TextAnswerAdmin(admin.ModelAdmin):
  list_display = ('question', '__str_text__')
  save_on_top = True


class OrderAdmin(admin.ModelAdmin):
  fieldsets = (
    ('Billing Info', {'fields': ('name', 'address', 'city', 'state', 'zip',
                                 'country')}),
    ('Contact Info', {'fields': ('email', 'phone')}),
    ('Order Info', {'fields': ('order_num', 'valid')}),
    ('Payment Info', {'fields': ('amount', 'payment_type', 'auth_code',
                                 'pnref', 'resp_msg', 'result',
                                 'already_paid_attendees')}),
  )
  list_display = ('order_num', 'date', 'name', 'address', 'city', 'state',
                  'zip', 'country', 'email', 'phone', 'amount', 'payment_type',
                  'valid')
  list_filter = ('date', 'payment_type', 'valid')
  save_on_top = True


class AttendeeAdmin(admin.ModelAdmin):
  fieldsets = (
    ('Attendee Info', {'fields': ('salutation', 'first_name', 'last_name',
                                  'title', 'org')}),
    ('Contact Info', {'fields': ('email', 'zip', 'phone')}),
    ('Badge Info', {'fields': ('badge_type', 'valid', 'checked_in')}),
    ('Items', {'fields': ('ordered_items', 'obtained_items')}),
    ('Misc', {'fields': ('promo', 'order', 'answers')}),
  )
  list_display = ('id', 'first_name', 'last_name', 'email', 'zip',
                  'badge_type', 'valid', 'checked_in', 'order', 'promo')
  list_filter = ('badge_type', 'valid', 'checked_in', 'promo', 'ordered_items')
  save_on_top = True


class CouponAdmin(admin.ModelAdmin):
  list_display = ('code', 'badge_type', 'order', 'used', 'max_attendees',
                  'expiration')
  list_filter = ('code', 'used', 'badge_type')
  save_on_top = True


class TicketAdmin(admin.ModelAdmin):
  list_display = ('name', 'description', 'type', 'price', 'priority', 'public',
                  'cash', 'upgradable', 'limit', 'start_date', 'end_date')
  list_filter = ('type', 'public', 'start_date', 'end_date')
  save_on_top = True


class UpgradeAdmin(admin.ModelAdmin):
  list_display = ('valid', 'attendee', 'old_badge_type', 'new_badge_type',
                  'old_order', 'new_order')
  list_filter = ['valid']
  save_on_top = True


admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(ListAnswer, ListAnswerAdmin)
admin.site.register(ListQuestion, ListQuestionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Reprint, ReprintAdmin)
admin.site.register(TextAnswer, TextAnswerAdmin)
admin.site.register(TextQuestion, TextQuestionAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Upgrade, UpgradeAdmin)
