from django.contrib import admin

from core import models


admin.site.register(models.Cliente)
admin.site.register(models.Sucursal)
admin.site.register(models.User)
admin.site.register(models.Categoria)
admin.site.register(models.Ingrediente)