from servidor import MAX_MENSAJE, validar_mensaje


def test_mensaje_valido():
    """
    Caso positivo:
    un mensaje normal debe ser aceptado.
    """
    resultado = validar_mensaje(b"Hola, mundo")

    assert resultado is True


def test_mensaje_vacio():
    """
    Caso negativo:
    un mensaje vacío debe ser rechazado.
    """
    resultado = validar_mensaje(b"")

    assert resultado is False


def test_mensaje_con_solo_espacios():
    """
    Caso negativo:
    un mensaje compuesto únicamente por espacios debe ser rechazazado.
    """
    resultado = validar_mensaje(b"     ")

    assert resultado is False

def test_mensaje_con_saltos_y_tabulaciones():
    """
    Caso negativo:
    tabulaciones y saltos de línea sin texto también deben rechazarse.
    """
    resultado = validar_mensaje(b"\n\t   ")

    assert resultado is False


def test_mensaje_con_longitud_maxima():
    """
    Caso límite positivo:
    un mensaje con exactamente MAX_MENSAJE caracteres debe aceptarse.
    """
    mensaje = b"A" * MAX_MENSAJE

    resultado = validar_mensaje(mensaje)

    assert resultado is True


def test_mensaje_demasiado_largo():
    """
    Caso negativo:
    un mensaje que supera MAX_MENSAJE debe ser rechazado.
    """
    mensaje = b"A" * (MAX_MENSAJE + 1)

    resultado = validar_mensaje(mensaje)

    assert resultado is False


def test_mensaje_no_es_bytes():
    """
    Caso negativo:
    el servidor recibe bytes desde recv(), por lo que un string
    no debe considerarse una entrada válida para esta función.
    """
    resultado = validar_mensaje("Hola")

    assert resultado is False


def test_mensaje_con_utf8_invalido():
    """
    Condición excepcional:
    bytes que no pueden decodificarse como UTF-8 deben rechazarse.
    """
    mensaje = b"\xff\xfe\xfa"

    resultado = validar_mensaje(mensaje)

    assert resultado is False

def test_mensaje_con_acentos():
    """
    Caso positivo:
    un mensaje UTF-8 válido con acentos debe ser aceptado.
    """
    mensaje = "¡Hola! ¿Cómo estás?".encode("utf-8")

    resultado = validar_mensaje(mensaje)

    assert resultado is True