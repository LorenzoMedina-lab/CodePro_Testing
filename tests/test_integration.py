import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest


IP_SERVIDOR = "127.0.0.1"
PUERTO_SERVIDOR = 5000

# Obtenemos la carpeta raíz del proyecto.
RUTA_PROYECTO = Path(__file__).resolve().parent.parent

# Construimos la ruta absoluta hacia servidor.py.
RUTA_SERVIDOR = RUTA_PROYECTO / "servidor.py"


def esperar_servidor(timeout=5):
    """
    Intenta conectarse repetidamente hasta comprobar que el servidor
    está escuchando.

    Evita utilizar un sleep fijo que podría resultar insuficiente
    en una computadora más lenta.
    """
    tiempo_limite = time.time() + timeout

    while time.time() < tiempo_limite:
        try:
            conexion = socket.create_connection(
                (IP_SERVIDOR, PUERTO_SERVIDOR),
                timeout=0.2,
            )
            conexion.close()
            return

        except OSError:
            time.sleep(0.1)

    raise RuntimeError(
        "El servidor no comenzó a escuchar dentro del tiempo esperado."
    )


@pytest.fixture
def servidor_en_ejecucion():
    """
    Inicia servidor.py antes de cada prueba de integración
    y lo detiene al terminar.

    Cada prueba puede ejecutarse de forma independiente.
    """
    proceso = subprocess.Popen(
        [sys.executable, str(RUTA_SERVIDOR)],
        cwd=RUTA_PROYECTO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        esperar_servidor()

        # Si el proceso terminó antes de tiempo, el servidor no inició.
        if proceso.poll() is not None:
            pytest.fail(
                "El proceso del servidor terminó inesperadamente."
            )

        yield proceso

    finally:
        # Detenemos el servidor aunque la prueba falle.
        proceso.terminate()

        try:
            proceso.wait(timeout=3)

        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(timeout=3)


def conectar_cliente():
    """
    Crea un cliente TCP conectado al servidor.
    """
    cliente = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    cliente.settimeout(2)

    cliente.connect(
        (IP_SERVIDOR, PUERTO_SERVIDOR)
    )

    return cliente


def cerrar_clientes(*clientes):
    """
    Cierra los sockets utilizados por una prueba.
    """
    for cliente in clientes:
        try:
            cliente.close()
        except OSError:
            pass


def recibir_hasta(cliente, contenidos, timeout=2):
    """
    Acumula bytes recibidos hasta encontrar todos los contenidos esperados
    o hasta superar el tiempo máximo.

    Esto es necesario porque TCP puede entregar varios mensajes juntos
    o dividir los datos en distintas llamadas a recv().
    """
    datos_recibidos = b""
    tiempo_limite = time.time() + timeout

    while time.time() < tiempo_limite:
        try:
            datos_recibidos += cliente.recv(2048)

            if all(
                contenido in datos_recibidos
                for contenido in contenidos
            ):
                return datos_recibidos

        except socket.timeout:
            break

    return datos_recibidos


def test_mensaje_llega_a_todos_los_demas_clientes(
    servidor_en_ejecucion,
):
    """
    Tres clientes se conectan.

    El cliente A envía un mensaje.
    B y C deben recibirlo.
    A no debe recibir su propio mensaje.
    """
    cliente_a = conectar_cliente()
    cliente_b = conectar_cliente()
    cliente_c = conectar_cliente()

    try:
        # Damos un instante al servidor para aceptar las tres conexiones.
        time.sleep(0.2)

        mensaje = b"Hola desde A"

        cliente_a.sendall(mensaje)

        recibido_b = cliente_b.recv(2048)
        recibido_c = cliente_c.recv(2048)

        assert recibido_b == mensaje
        assert recibido_c == mensaje

        # El emisor no debería recibir eco.
        cliente_a.settimeout(0.4)

        with pytest.raises(socket.timeout):
            cliente_a.recv(2048)

    finally:
        cerrar_clientes(
            cliente_a,
            cliente_b,
            cliente_c,
        )


def test_varios_clientes_envian_simultaneamente(
    servidor_en_ejecucion,
):
    """
    Dos clientes envían mensajes casi al mismo tiempo.

    El tercer cliente debe recibir ambos mensajes,
    sin pérdida y sin duplicación.
    """
    cliente_a = conectar_cliente()
    cliente_b = conectar_cliente()
    cliente_c = conectar_cliente()

    try:
        time.sleep(0.2)

        mensaje_a = b"[mensaje-A]"
        mensaje_b = b"[mensaje-B]"

        # La barrera hace que ambos hilos comiencen el envío
        # aproximadamente al mismo tiempo.
        barrera = threading.Barrier(3)

        def enviar(cliente, mensaje):
            barrera.wait()
            cliente.sendall(mensaje)

        hilo_a = threading.Thread(
            target=enviar,
            args=(cliente_a, mensaje_a),
        )

        hilo_b = threading.Thread(
            target=enviar,
            args=(cliente_b, mensaje_b),
        )

        hilo_a.start()
        hilo_b.start()

        # Libera simultáneamente ambos hilos.
        barrera.wait()

        hilo_a.join()
        hilo_b.join()

        datos_c = recibir_hasta(
            cliente_c,
            [mensaje_a, mensaje_b],
        )

        assert mensaje_a in datos_c
        assert mensaje_b in datos_c

        # Cada mensaje debe aparecer una sola vez.
        assert datos_c.count(mensaje_a) == 1
        assert datos_c.count(mensaje_b) == 1

    finally:
        cerrar_clientes(
            cliente_a,
            cliente_b,
            cliente_c,
        )


def test_mensajes_del_mismo_cliente_mantienen_el_orden(
    servidor_en_ejecucion,
):
    """
    TCP mantiene el orden de los bytes enviados por una misma conexión.

    El receptor debe obtener primero el primer mensaje
    y luego el segundo, aunque ambos puedan llegar juntos en recv().
    """
    emisor = conectar_cliente()
    receptor = conectar_cliente()

    try:
        time.sleep(0.2)

        primer_mensaje = b"[primero]"
        segundo_mensaje = b"[segundo]"

        emisor.sendall(primer_mensaje)
        time.sleep(0.1)
        emisor.sendall(segundo_mensaje)

        datos = recibir_hasta(
            receptor,
            [primer_mensaje, segundo_mensaje],
        )

        assert datos == primer_mensaje + segundo_mensaje

    finally:
        cerrar_clientes(
            emisor,
            receptor,
        )


def test_servidor_continua_tras_desconexion_de_un_cliente(
    servidor_en_ejecucion,
):
    """
    Se conectan tres clientes.

    B se desconecta directamente.
    A envía un mensaje.
    C debe continuar recibiéndolo.
    """
    cliente_a = conectar_cliente()
    cliente_b = conectar_cliente()
    cliente_c = conectar_cliente()

    try:
        time.sleep(0.2)

        # El cliente se cierra sin utilizar el comando /exit
        # del programa cliente.py.
        cliente_b.close()

        # Permitimos que el servidor detecte la desconexión.
        time.sleep(0.2)

        mensaje = b"El servidor sigue funcionando"

        cliente_a.sendall(mensaje)

        recibido_c = cliente_c.recv(2048)

        assert recibido_c == mensaje

        # El proceso del servidor todavía debe estar activo.
        assert servidor_en_ejecucion.poll() is None

    finally:
        cerrar_clientes(
            cliente_a,
            cliente_c,
        )


def test_mensaje_invalido_no_se_retransmite(
    servidor_en_ejecucion,
):
    """
    Caso negativo de integración:

    Un mensaje compuesto solo por espacios debe ser rechazado
    y no debe llegar al otro cliente.
    """
    emisor = conectar_cliente()
    receptor = conectar_cliente()

    try:
        time.sleep(0.2)

        receptor.settimeout(0.5)

        emisor.sendall(b"     ")

        with pytest.raises(socket.timeout):
            receptor.recv(2048)

        # El rechazo no debe detener el servidor.
        assert servidor_en_ejecucion.poll() is None

    finally:
        cerrar_clientes(
            emisor,
            receptor,
        )