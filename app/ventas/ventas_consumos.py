from django.core.exceptions import ObjectDoesNotExist

import pandas as pd
import datetime
from core import models


# def registrar(df_ventas, sucursal):
#     df_ventas = df_ventas
#     sucursal = sucursal

#     return True


def registrar(df_ventas, sucursal):

    total_ventas_consumos = []
    ayer = datetime.date.today() - datetime.timedelta(days=1)
    productos_no_registrados = []

    for (sucursal_id, caja_id, codigo_pos, nombre, unidades, importe) in df_ventas.itertuples(index=False, name=None):

        # Checamos si existe la receta en la base de datos
        try:
            receta = models.Receta.objects.get(codigo_pos=codigo_pos, sucursal=sucursal)

        # Si la receta no existe
        except ObjectDoesNotExist:
            #sin_registro = [sucursal.slug, codigo_pos, nombre]
            sin_registro = models.ProductoSinRegistro.objects.create(
                sucursal=sucursal.slug,
                codigo_pos=codigo_pos,
                caja=caja_id,
                nombre=nombre
                )
            productos_no_registrados.append(sin_registro)

        """
        -----------------------------------------------------------
        Registrar la venta de la receta
        -----------------------------------------------------------
        """
        receta = models.Receta.objects.get(codigo_pos=codigo_pos, sucursal=sucursal)
        caja = models.Caja.objects.get(id=caja_id)

        venta = models.Venta.objects.create(
            receta=receta,
            sucursal=sucursal,
            fecha=ayer,
            unidades=unidades,
            importe=importe,
            caja=caja
        )


        """
        -----------------------------------------------------------
        Registrar el consumo de ingredientes generado por la venta
        -----------------------------------------------------------
        """
        # Seleccionamos los ingredientes de la receta
        ingredientes_receta = receta.ingredientes.all()

        # Tomamos el volumen consumido por ingrediente y lo multiplicamos por las unidades vendidas
        for item in ingredientes_receta:
            consumos = []
            ingrediente = item
            it = models.IngredienteReceta.objects.get(receta=receta, ingrediente=ingrediente)
            volumen = it.volumen
            volumen_total = volumen * unidades

            # Guardamos el consumo en la base de datos
            consumo = models.ConsumoRecetaVendida.objects.create(
                ingrediente=ingrediente,
                receta=receta,
                venta=venta,
                fecha=ayer,
                volumen=volumen_total
            )

            #consumos.append(consumo)
            consumos.append(str(consumo))

        #total_ventas_consumos.append({'venta': venta, 'consumos': consumos})
        total_ventas_consumos.append({'venta': str(venta), 'consumos': consumos})
        
    return {'ventas_consumos': total_ventas_consumos, 'productos_no_registrados': productos_no_registrados}
        









