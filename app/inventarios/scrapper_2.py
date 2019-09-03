
from bs4 import BeautifulSoup
import requests


def get_data_sat(folio):

    try:
        url_sat = BeautifulSoup(requests.get('https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3='+folio).text, 'lxml')
        tables = url_sat.find_all('table')

        #---------------------- DATOS MARBETE -----------------------
        trs = url_sat.find_all('tr')

        # Tipo de marbete
        tds = trs[2].find_all('td')
        tipo_marbete = tds[1].text

        # Folio Marbete
        tds = trs[3].find_all('td')
        folio_id = tds[1].text

        # Fecha de elaboración
        tds = trs[4].find_all('td')
        fecha_elaboracion_marbete = tds[1].text

        # Lote de producción
        tds = trs[5].find_all('td')
        lote_produccion_marbete = tds[1].text

        # URL
        url = 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3='+folio

        #----------------------- DATOS DEL PRODUCTO ----------------------

        # Si la botella es importada:
        # - Tomamos los campos 'fecha_importacion' y 'numero_pedimento'

        if folio[0] == 'I':

            trs = tables[3].find_all('tr')

            # Nombre o marca
            tds = trs[2].find_all('td')
            nombre_marca = tds[1].text

            # Tipo producto
            tds = trs[3].find_all('td')
            tipo_producto = tds[1].text

            # Graduación alcohólica
            tds = trs[4].find_all('td')
            graduacion_alcoholica = tds[1].text

            # Capacidad
            tds = trs[5].find_all('td')
            capacidad = tds[1].text

            # Origen del producto
            tds = trs[6].find_all('td')
            origen = tds[1].text

            # Fecha de importación
            tds = trs[7].find_all('td')
            fecha_importacion = tds[1].text

            # Número de pedimento
            tds = trs[8].find_all('td')
            numero_pedimento = tds[1].text

            #---------------- DATOS DEL PRODUCTOR, FABRICANTE, ENVASADOR O IMPORTADOR -----------------
            trs = tables[6].find_all('tr')

            # Nombre
            tds = trs[2].find_all('td')
            nombre_fabricante = tds[1].text

            # RFC
            tds = trs[3].find_all('td')
            rfc_fabricante = tds[1].text

            data = {
                'folio': folio_id,
                'tipo_marbete': tipo_marbete,
                'fecha_elaboracion_marbete': fecha_elaboracion_marbete,
                'lote_produccion_marbete': lote_produccion_marbete,
                'url': url,
                'nombre_marca': nombre_marca,
                'tipo_producto': tipo_producto,
                'graduacion_alcoholica': graduacion_alcoholica,
                'capacidad': capacidad,
                'origen_del_producto': origen,
                'fecha_importacion': fecha_importacion,
                'numero_pedimento': numero_pedimento,
                'nombre_fabricante': nombre_fabricante,
                'rfc_fabricante': rfc_fabricante
            }

            result = {
                'status': 1,
                'marbete': data
            }

            return result

        #------------------------------------------------------------------------
        # Si la botella es nacional:
        # - Tomamos los campos 'fecha_envasado' y 'lote_produccion'

        else:

            trs = tables[3].find_all('tr')

            # Nombre o marca
            tds = trs[2].find_all('td')
            nombre_marca = tds[1].text

            # Tipo producto
            tds = trs[3].find_all('td')
            tipo_producto = tds[1].text

            # Graduación alcohólica
            tds = trs[4].find_all('td')
            graduacion_alcoholica = tds[1].text

            # Capacidad
            tds = trs[5].find_all('td')
            capacidad = tds[1].text

            # Origen del producto
            tds = trs[6].find_all('td')
            origen = tds[1].text

            # Fecha de envasado
            tds = trs[7].find_all('td')
            fecha_envasado = tds[1].text

            # Lote de produccion
            tds = trs[8].find_all('td')
            lote_produccion = tds[1].text

            #---------------- DATOS DEL PRODUCTOR, FABRICANTE, ENVASADOR O IMPORTADOR -----------------
            trs = tables[6].find_all('tr')

            # Nombre
            tds = trs[2].find_all('td')
            nombre_fabricante = tds[1].text

            # RFC
            tds = trs[3].find_all('td')
            rfc_fabricante = tds[1].text

            data = {
                'folio': folio_id,
                'tipo_marbete': tipo_marbete,
                'fecha_elaboracion_marbete': fecha_elaboracion_marbete,
                'lote_produccion_marbete': lote_produccion_marbete,
                'url': url,
                'nombre_marca': nombre_marca,
                'tipo_producto': tipo_producto,
                'graduacion_alcoholica': graduacion_alcoholica,
                'capacidad': capacidad,
                'origen_del_producto': origen,
                'fecha_envasado': fecha_envasado,
                'lote_produccion': lote_produccion,
                'nombre_fabricante': nombre_fabricante,
                'rfc_fabricante': rfc_fabricante
            }

            result = {
                'status': 1,
                'marbete': data
            }

            return result


    except(ConnectionError, Exception):

        result = {
            'status': 0
        }

        return result
