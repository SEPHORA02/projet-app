from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Patient, PhysiologicalData, EnvironmentalData, Alert


class PatientInline(admin.StackedInline):
    model = Patient
    can_delete = False
    verbose_name_plural = "Profil Patient"


class UserAdmin(BaseUserAdmin):
    inlines = (PatientInline,)


# Désenregistrer l'admin par défaut
admin.site.unregister(User)

# Réenregistrer avec notre admin personnalisé
admin.site.register(User, UserAdmin)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'age',
        'location',
        'sex',
        'phone_number',
        'is_active',
        'sensors_status',
        'created_at',
    )
    list_filter = ('is_active', 'sex', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'location', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PhysiologicalData)
class PhysiologicalDataAdmin(admin.ModelAdmin):
    list_display = ('patient', 'heart_rate', 'oxygen_saturation', 'temperature', 'recorded_at')
    list_filter = ('recorded_at', 'patient')
    search_fields = ('patient__user__username',)
    date_hierarchy = 'recorded_at'


@admin.register(EnvironmentalData)
class EnvironmentalDataAdmin(admin.ModelAdmin):
    list_display = ('patient', 'air_quality_index', 'co2_level', 'humidity', 'pm25', 'recorded_at')
    list_filter = ('recorded_at', 'patient')
    search_fields = ('patient__user__username',)
    date_hierarchy = 'recorded_at'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'patient', 'alert_type', 'level', 'is_read', 'created_at')
    list_filter = ('alert_type', 'level', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'patient__user__username')
    date_hierarchy = 'created_at'
    list_editable = ('is_read',)

