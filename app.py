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
        server = fmrest.Server('https://a049937.fmphost.com',
                               user='Admin',
                               password='speedprint',
                               database='speed2',
                               layout='productos',
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


def datos_producto(registro):
    return {"id_registro":registro[7],"nombre": registro[0], "precio": registro[1], "material": registro[2],
            "unidad": registro[3],
            "color": registro[4], "altura": registro[5], "anchura": registro[6]}


def formato_producto(payload):
    return {"nombre": payload['nombre'], "precio": payload['precio'],
            "material": payload['material'],
            "unidad": payload['unidad'],
            "color": payload['color'], "altura": payload['altura'],
            "anchura": payload['anchura']}


def pagina_404(error):
    return "<h1>La pagina no existe</h1>", 404


@app.route('/')
def hello_world():
    return 'Hello, World!'
