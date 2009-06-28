from django.contrib import admin
from reg6.models import Answer
from reg6.models import Attendee
from reg6.models import Coupon
from reg6.models import Item
from reg6.models import Order
from reg6.models import PromoCode
from reg6.models import Question
from reg6.models import Ticket

class AnswerInline(admin.TabularInline):
  model = Answer
  extra = 3

class PromoCodeOptions(admin.ModelAdmin):
  list_display = ('name', 'description', 'price_modifier', 'active',
      'start_date', 'end_date')
  list_filter = ('active', 'start_date', 'end_date')
  save_on_top = True

class QuestionOptions(admin.ModelAdmin):
  save_on_top = True
  model = Question
  inlines = [AnswerInline]

class ItemOptions(admin.ModelAdmin):
  list_display = ('name', 'description', 'price', 'active', 'pickup', 'promo')
  list_filter = ('active', 'pickup', 'promo')
  save_on_top = True

class AnswerOptions(admin.ModelAdmin):
  list_display = ('question', '__str_text__')
  save_on_top = True

class OrderOptions(admin.ModelAdmin):
  fieldsets = (
    ('Billing Info', {'fields': ('name', 'address', 'city', 'state', 'zip',
                                 'country')}),
    ('Contact Info', {'fields': ('email', 'phone')}),
    ('Order Info', {'fields': ('order_num', 'valid')}),
    ('Payment Info', {'fields': ('amount', 'payment_type', 'auth_code',
                                 'resp_msg', 'result')}),
  )
  list_display = ('order_num', 'date', 'name', 'address', 'city', 'state',
      'zip', 'country', 'email', 'phone', 'amount', 'payment_type', 'valid')
  list_filter = ('date', 'payment_type', 'valid')
  save_on_top = True

class AttendeeOptions(admin.ModelAdmin):
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
  list_filter = ('badge_type', 'valid', 'checked_in', 'promo')
  save_on_top = True

class CouponOptions(admin.ModelAdmin):
  list_display = ('code', 'badge_type', 'order', 'used', 'max_attendees',
      'expiration')
  list_filter = ('code', 'used', 'badge_type')
  save_on_top = True

class TicketOptions(admin.ModelAdmin):
  list_display = ('name', 'description', 'type', 'price', 'public',
    'start_date', 'end_date')
  list_filter = ('type', 'public', 'start_date', 'end_date')
  save_on_top = True

admin.site.register(PromoCode, PromoCodeOptions)
admin.site.register(Question, QuestionOptions)
admin.site.register(Item, ItemOptions)
admin.site.register(Answer, AnswerOptions)
admin.site.register(Order, OrderOptions)
admin.site.register(Attendee, AttendeeOptions)
admin.site.register(Coupon, CouponOptions)
admin.site.register(Ticket, TicketOptions)

