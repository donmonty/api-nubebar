from rest_framework import permissions


class PermisoSucursal(permissions.BasePermission):
	""" Checa que el usuario tenga asignada una sucursal """

	def has_permission(self, request, view):
		user = self.request.user
		sucursales_usuario = user.sucursales.all()

		lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

		if request.data['sucursal'] in lista_sucursales:
			return True

		return False