import fmrest
import urllib3
from fmrest.utils import TIMEOUT
from fmrest.exceptions import FileMakerError, RequestException
from requests.exceptions import RequestException
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/connect', methods=['POST'])
def connect():
    # connect to the FileMaker Server
    urllib3.disable_warnings()
    fmrest.utils.TIMEOUT = 30
    try:
        server = fmrest.Server('https://a0410012.fmphost.com/',
                               user='Invitado',
                               password='speed',
                               database='Productos',
                               layout='Lista de precios',
                               verify_ssl=True,
                               api_version='vLatest'
                               )
        server.login()
        return server
    except ValueError as err:
        return 'Failed to connect to server. Please check server credentials and status and try again\\n\\n' + str(
            err), 500
    except FileMakerError as err:
        return str(err), 500
    except RequestException as err:
        return 'There was an error connecting to the server, the request timed out\\n\\n' + str(err), 500


fm = connect()
records = fm.get_records()
print(records)


@app.route('/producto/<id_producto>', methods=['GET'])
def consultar_producto(id_producto):
    fms = connect()
    try:
        registro = fms.get_record(id_producto).values()
        if registro is not None:
            informacion = datos_producto(registro)
            return jsonify({"mensaje": "Registro encontrado", "datos": informacion})
        else:
            return jsonify({"mensaje": "Hubo un error al realizar la consulta"})
    except RequestException as _:
        return jsonify({"Error": "No se pudo establecer conexión con la base de datos"})
    except fmrest.exceptions.FileMakerError as _:
        return jsonify({"Error": "Registro no encontrado"})
    finally:
        fms.logout()


@app.route('/producto', methods=['GET'])
def consultar_productos():
    fms = connect()
    try:
        registros = fms.get_records()
        if registros is not None:
            productos = []
            for producto in registros:
                valores = producto.values()
                productos.append(datos_producto(valores))
            return jsonify({"mensaje": "Registro encontrado", "productos": productos})
        else:
            return jsonify({"Error": "Hubo un error al realizar la consulta"})
    except RequestException as _:
        return jsonify({"Error": "No se pudo establecer conexión con la base de datos"})
    finally:
        fms.logout()


@app.route('/producto/nombre/<producto>', methods=['GET'])
def encontrar_productos(producto):
    fms = connect()
    try:
        find_query = [{'nombre': producto}]
        foundset = fms.find(find_query)
        if foundset is not None:
            valores = foundset[0].values()
            return jsonify({"mensaje": "Registro encontrado", "productos": datos_producto(valores)})
        else:
            return jsonify({"Error": "Hubo un error al realizar la consulta"})
    except RequestException as _:
        return jsonify({"Error": "No se pudo establecer conexión con la base de datos"})
    except fmrest.exceptions.FileMakerError as _:
        return jsonify({"Errorres": "Registro no encontrado"})
    finally:
        fms.logout()


@app.route('/producto/registrar', methods=['POST'])
def agregar_producto():
    fms = connect()
    try:
        if request is not None:
            fms.create_record(formato_producto(request.json))
            return jsonify({"mensaje": "Producto registrado"})
        else:
            return jsonify({"mensaje": "No se hallaron datos en la solicitud"})
    except RequestException as ex:
        return jsonify({"Error": ex})
    except KeyError as _:
        return jsonify({"Error": "El registro no contiene los datos requeridos"})
    finally:
        fms.logout()


@app.route('/producto/actualizar/<id_producto>', methods=['PUT'])
def actualizar_producto(id_producto):
    fms = connect()
    try:
        if request is not None:
            fms.edit_record(id_producto, formato_producto(request.json))
            return jsonify({"mensaje": "Producto actualizado"})
        else:
            return
    except RequestException as _:
        return jsonify({"Error": "No se logró establecer conexión con la base de datos"})
    except KeyError as _:
        return jsonify({"Error": "El registro no contiene los datos requeridos"})
    except fmrest.exceptions.FileMakerError as _:
        return jsonify({"Error": "Registro no encontrado"})
    finally:
        fms.logout()


@app.route('/producto/eliminar/<id_producto>', methods=['DELETE'])
def eliminar_producto(id_producto):
    fms = connect()
    try:
        fms.delete_record(id_producto)
        return jsonify({"mensaje": "Producto eliminado"})
    except RequestException as _:
        return jsonify({"Error": "No se logró establecer conexión con la base de datos"})
    except fmrest.exceptions.FileMakerError as _:
        return jsonify({"mensaje": "Registro no encontrado"})
    finally:
        fms.logout()


'''def datos_producto(registro):
    return {"nombre": registro[0], "precio": registro[1], "material": registro[2],
            "unidad": registro[3],
            "color": registro[4], "altura": registro[5], "anchura": registro[6]}

'''


def datos_producto(registro):
    return {"Codigo": registro[0], "Nombre": registro[1], "Descripcion": registro[2],
            "Medida": registro[3], "Precio P": registro[4], "Precio M": registro[5]}


def formato_producto(payload):
    return {"nombre": payload['nombre'], "precio": payload['precio'],
            "material": payload['material'],
            "unidad": payload['unidad'],
            "color": payload['color'], "altura": payload['altura'],
            "anchura": payload['anchura']}


def pagina_404(error):
    return "<h1>La pagina no existe</h1>", 404


if __name__ == '__main__':
    app.register_error_handler(404, pagina_404)
    app.run()
