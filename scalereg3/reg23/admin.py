from django.contrib import admin

from .models import Ticket


class TicketAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'ticket_type', 'price', 'public',
                    'cash', 'upgradable', 'start_date', 'end_date')
    list_filter = ('ticket_type', 'public', 'start_date', 'end_date')
    save_on_top = True


admin.site.register(Ticket, TicketAdmin)
