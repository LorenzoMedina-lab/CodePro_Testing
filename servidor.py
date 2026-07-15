import socket  # Interfaz de Python para la API de sockets de C del sistema operativo.
import select  # Acceso a la llamada al sistema (syscall) select() para multiplexación de I/O.

# 0.0.0.0 indica al kernel que el socket debe escuchar en todas las interfaces de red disponibles
# (localhost, Wi-Fi, Ethernet).
IP = "0.0.0.0"
PUERTO = 5000  # Puerto de escucha

# Cantidad máxima de caracteres permitidos en un mensaje.
MAX_MENSAJE = 500


def validar_mensaje(message):
    """
    Valida que el mensaje no esté vacío, no contenga solo espacios
    y no supere la longitud máxima permitida.
    """

    # recv() devuelve bytes, por eso primero verificamos el tipo.
    if not isinstance(message, bytes):
        return False

    if not message:
        return False

    try:
        texto = message.decode("utf-8").strip()
    except UnicodeDecodeError:
        return False

    if not texto:
        return False

    if len(texto) > MAX_MENSAJE:
        return False

    return True


def eliminar_cliente(lista_sockets, cliente):
    """
    Elimina un cliente de la lista y cierra su socket.
    """

    if cliente in lista_sockets:
        lista_sockets.remove(cliente)

    try:
        cliente.close()
    except Exception:
        pass


def broadcast(lista_sockets, servidor, emisor, message):
    """
    Envía el mensaje a todos los clientes conectados,
    excepto al servidor y al cliente que lo envió.
    """

    # Recorremos una copia porque la lista puede cambiar
    # si un cliente falla durante el envío.
    for client in lista_sockets.copy():

        if client != servidor and client != emisor:

            try:
                client.send(message)

            except Exception:
                # Si el envío falla, asumimos que el cliente
                # se desconectó abruptamente.
                eliminar_cliente(lista_sockets, client)


def main():
    # AF_INET especifica la familia de direcciones IPv4.
    # SOCK_STREAM especifica el protocolo TCP
    # orientado a conexión y flujo de bytes.
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # SOL_SOCKET y SO_REUSEADDR manipulan las opciones del socket
    # a nivel del sistema operativo.
    # SO_REUSEADDR permite reiniciar rápidamente el servidor
    # sin esperar a que el SO libere completamente el puerto.
    servidor.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    # bind() asocia el file descriptor del socket
    # con la IP y el puerto específicos.
    servidor.bind((IP, PUERTO))

    # listen(5) deja el servidor listo para aceptar conexiones.
    # El número 5 indica cuántas conexiones pendientes
    # puede mantener la cola del sistema operativo.
    servidor.listen(5)

    # Lista que almacena los file descriptors.
    # El servidor es el primer elemento porque queremos monitorear
    # nuevas conexiones además de los mensajes de los clientes.
    lista_sockets = [servidor]

    print(f"Chat en línea. Escuchando en {IP}:{PUERTO}")

    # Bucle infinito del servidor:
    # el corazón del I/O Multiplexing.
    while True:

        # select() bloquea el hilo hasta que al menos un socket
        # esté listo para lectura o presente un error.
        read_sockets, _, exception_sockets = select.select(
            lista_sockets,
            [],
            lista_sockets
        )

        # Se recorren únicamente los sockets
        # que tienen actividad.
        for notified_socket in read_sockets:

            # Si el socket activo es el servidor,
            # significa que hay una nueva conexión.
            if notified_socket == servidor:

                # accept() crea un nuevo socket dedicado
                # exclusivamente al cliente conectado.
                client_socket, client_address = servidor.accept()

                lista_sockets.append(client_socket)

                print(
                    f"Nueva conexión detectada desde: {client_address}"
                )

            # Si no es el servidor, es un cliente enviando datos.
            else:

                try:
                    # recv() lee hasta 2048 bytes
                    # del buffer de red.
                    message = notified_socket.recv(2048)

                    # Si recv() devuelve 0 bytes,
                    # el cliente cerró la conexión.
                    if not message:

                        print("Cliente desconectado limpiamente.")

                        eliminar_cliente(
                            lista_sockets,
                            notified_socket
                        )

                        continue

                    # Verificamos que el mensaje sea válido
                    # antes de retransmitirlo.
                    if not validar_mensaje(message):

                        print("Mensaje rechazado.")

                        continue

                    # Enviamos el mensaje a todos los demás clientes.
                    broadcast(
                        lista_sockets,
                        servidor,
                        notified_socket,
                        message
                    )

                # Captura errores como ConnectionResetError,
                # por ejemplo si un cliente cierra su terminal
                # abruptamente.
                except Exception as error:

                    print(f"💥 Error en la conexión: {error}")

                    eliminar_cliente(
                        lista_sockets,
                        notified_socket
                    )

        # Si select() detecta sockets con errores,
        # se eliminan para que no afecten al resto del servidor.
        for notified_socket in exception_sockets:

            eliminar_cliente(
                lista_sockets,
                notified_socket
            )


# Evita que el servidor se ejecute automáticamente
# cuando pytest importe este archivo.
if __name__ == "__main__":
    main()