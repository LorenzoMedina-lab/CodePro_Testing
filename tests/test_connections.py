from unittest.mock import Mock # Esta importación permite crear objetos simulados para pruebas unitarias.

from servidor import broadcast, eliminar_cliente # Importamos las funciones que vamos a probar desde el módulo servidor.py.


def test_eliminar_cliente_existente():
    """
    Caso positivo:
    el cliente debe eliminarse de la lista y su socket debe cerrarse.
    """
    servidor = Mock() # Creamos un objeto simulado para representar el socket del servidor.
    cliente = Mock() # Creamos un objeto simulado para representar el socket del cliente.

    lista_sockets = [servidor, cliente]

    eliminar_cliente(lista_sockets, cliente)

    assert cliente not in lista_sockets
    cliente.close.assert_called_once() # Verificamos que el método close() del socket del cliente haya sido llamado exactamente una vez. Esto asegura que los recursos del socket se liberaron correctamente.


def test_eliminar_cliente_inexistente():
    """
    Caso negativo:
    eliminar un cliente que no está en la lista no debe romper el servidor.

    Aunque no esté en la lista, se intenta cerrar su socket para asegurar
    que sus recursos sean liberados.
    """
    servidor = Mock()
    cliente_existente = Mock()
    cliente_inexistente = Mock()

    lista_sockets = [servidor, cliente_existente]

    eliminar_cliente(lista_sockets, cliente_inexistente)

    assert lista_sockets == [servidor, cliente_existente]
    cliente_inexistente.close.assert_called_once()


def test_broadcast_envia_a_los_demas_clientes():
    """
    Caso positivo:
    el mensaje debe llegar a todos los clientes excepto al emisor
    y al socket principal del servidor.
    """
    servidor = Mock()
    emisor = Mock()
    cliente_b = Mock()
    cliente_c = Mock()

    lista_sockets = [
        servidor,
        emisor,
        cliente_b,
        cliente_c,
    ]

    mensaje = b"Hola a todos"

    broadcast(
        lista_sockets,
        servidor,
        emisor,
        mensaje,
    )

    cliente_b.send.assert_called_once_with(mensaje)
    cliente_c.send.assert_called_once_with(mensaje)


def test_broadcast_no_envia_al_emisor():
    """
    El cliente que envió el mensaje no debe recibir su propio mensaje.
    """
    servidor = Mock()
    emisor = Mock()
    receptor = Mock()

    lista_sockets = [
        servidor,
        emisor,
        receptor,
    ]

    broadcast(
        lista_sockets,
        servidor,
        emisor,
        b"Mensaje",
    )

    emisor.send.assert_not_called()


def test_broadcast_no_envia_al_socket_del_servidor():
    """
    El socket principal del servidor solo acepta conexiones;
    no debe recibir mensajes mediante send().
    """
    servidor = Mock()
    emisor = Mock()
    receptor = Mock()

    lista_sockets = [
        servidor,
        emisor,
        receptor,
    ]

    broadcast(
        lista_sockets,
        servidor,
        emisor,
        b"Mensaje",
    )

    servidor.send.assert_not_called()


def test_broadcast_elimina_cliente_si_el_envio_falla():
    """
    Condición excepcional:
    si un cliente falla durante send(), debe eliminarse de la lista
    y cerrarse sin afectar a los demás clientes.
    """
    servidor = Mock()
    emisor = Mock()
    cliente_con_error = Mock()
    cliente_activo = Mock()

    # Simulamos una desconexión o Broken Pipe durante el envío.
    cliente_con_error.send.side_effect = OSError(
        "Cliente desconectado"
    )

    lista_sockets = [
        servidor,
        emisor,
        cliente_con_error,
        cliente_activo,
    ]

    mensaje = b"Mensaje importante"

    broadcast(
        lista_sockets,
        servidor,
        emisor,
        mensaje,
    )

    assert cliente_con_error not in lista_sockets
    cliente_con_error.close.assert_called_once()

    # El fallo de un cliente no debe impedir el envío al siguiente.
    cliente_activo.send.assert_called_once_with(mensaje)