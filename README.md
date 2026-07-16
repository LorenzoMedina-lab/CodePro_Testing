# Sock-it-to-me Chat — Pruebas automatizadas

Este proyecto implementa un servidor de chat TCP en Python capaz de manejar múltiples clientes conectados mediante sockets.

El desafío consistió en refactorizar el servidor lo mínimo necesario para hacerlo testeable e implementar pruebas unitarias y de integración utilizando `pytest`.

El objetivo principal fue comprobar que:

* Los mensajes válidos se procesen correctamente.
* Los mensajes inválidos sean rechazados.
* Los clientes puedan conectarse y desconectarse sin bloquear el servidor.
* Los mensajes se distribuyan correctamente entre múltiples clientes.
* Los mensajes no se pierdan ni se dupliquen en los escenarios probados.
* El servidor continúe funcionando después de una desconexión.

---

## Tecnologías utilizadas

* Python 3
* `socket`
* `select`
* `threading`
* `subprocess`
* `pytest`
* `unittest.mock`

El módulo `threading` se utiliza únicamente en una prueba de integración para simular clientes enviando mensajes simultáneamente.

El servidor conserva su implementación basada en `socket` y `select`.

---

## Estructura del proyecto

```text
CODEPRO_TESTING/
├── evidencias/
├── tests/
│   ├── test_connections.py
│   ├── test_integration.py
│   └── test_validation.py
├── .gitignore
├── cliente.py
├── servidor.py
└── README.md

---

## Refactorización del servidor

La implementación original ejecutaba toda la lógica directamente al importar el archivo.

Esto dificultaba las pruebas unitarias porque importar `servidor.py` iniciaba inmediatamente el socket y el ciclo infinito del servidor.

Para hacerlo testeable, se realizaron cambios mínimos:

* Se creó la función `validar_mensaje()`.
* Se creó la función `eliminar_cliente()`.
* Se creó la función `broadcast()`.
* La ejecución principal se movió a `main()`.
* Se agregó el punto de entrada:

```python
if __name__ == "__main__":
    main()
```

Esto permite importar las funciones desde las pruebas sin iniciar automáticamente el servidor.

---

# Instalación

## 1. Crear un entorno virtual

En PowerShell:

```powershell
python -m venv venv
```

Activar el entorno:

```powershell
.\venv\Scripts\Activate.ps1
```

En caso de que PowerShell bloquee la ejecución de scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Luego vuelve a activar el entorno:

```powershell
.\venv\Scripts\Activate.ps1
```

## 2. Instalar Pytest

```powershell
python -m pip install pytest
```

Verificar la instalación:

```powershell
python -m pytest --version
```

---

# Ejecución de las pruebas

Todas las pruebas deben ejecutarse desde la carpeta raíz del proyecto:

```text
C:\Users\Lorenzo Medina\Desktop\CodePro_Testing
```

## Ejecutar todas las pruebas

```powershell
python -m pytest -v
```

## Ejecutar solo las pruebas de validación

```powershell
python -m pytest tests/test_validation.py -v
```

## Ejecutar solo las pruebas de conexiones

```powershell
python -m pytest tests/test_connections.py -v
```

## Ejecutar solo las pruebas de integración

```powershell
python -m pytest tests/test_integration.py -v
```

---

# Aplicación de TDD

Se aplicó la metodología TDD a la función `validar_mensaje()`.

El ciclo utilizado fue:

```text
RED → GREEN → REFACTOR
```

## Primera fase RED

Inicialmente se definió una implementación incompleta:

```python
def validar_mensaje(message):
    return True
```

Luego se escribieron tres pruebas:

* Un mensaje válido debe aceptarse.
* Un mensaje vacío debe rechazarse.
* Un mensaje compuesto únicamente por espacios debe rechazarse.

Resultado:

```text
1 passed
2 failed
```

La prueba de mensaje válido pasó, pero los mensajes vacíos y los mensajes con espacios fueron aceptados incorrectamente.

Esto confirmó que la funcionalidad todavía no estaba implementada.

---

## Primera fase GREEN

Se agregó la implementación mínima:

```python
def validar_mensaje(message):
    if not message:
        return False

    texto = message.decode("utf-8").strip()

    if not texto:
        return False

    return True
```

Resultado:

```text
3 passed
```

La función comenzó a:

* aceptar mensajes válidos;
* rechazar mensajes vacíos;
* rechazar mensajes compuestos únicamente por espacios.

---

## Segundo ciclo RED

Posteriormente se agregaron pruebas para comportamientos adicionales:

* mensajes demasiado largos;
* valores que no son de tipo `bytes`;
* secuencias de bytes con UTF-8 inválido.

Resultado:

```text
5 passed
3 failed
```

Los fallos encontrados fueron:

* no se comprobaba la longitud máxima;
* una entrada de tipo `str` producía `AttributeError`;
* una codificación UTF-8 inválida producía `UnicodeDecodeError`.

---

## Segundo GREEN y REFACTOR

Se completó la función agregando:

* validación del tipo de dato;
* manejo de `UnicodeDecodeError`;
* validación de longitud máxima;
* uso de la constante `MAX_MENSAJE`;
* rechazo de mensajes vacíos o sin contenido visible.

Resultado:

```text
8 passed
```

Luego se añadió también una prueba para mensajes con acentos y caracteres UTF-8 válidos.

La suite final de validación quedó con:

```text
9 passed
```

La implementación final mantiene una lógica sencilla y evita duplicaciones innecesarias.

---

# Pruebas unitarias de validación

El archivo `tests/test_validation.py` contiene pruebas para los siguientes escenarios:

| Prueba                         | Comportamiento esperado |
| ------------------------------ | ----------------------- |
| Mensaje normal                 | Se acepta               |
| Mensaje vacío                  | Se rechaza              |
| Mensaje con espacios           | Se rechaza              |
| Saltos de línea y tabulaciones | Se rechazan             |
| Longitud máxima exacta         | Se acepta               |
| Longitud superior al máximo    | Se rechaza              |
| Entrada que no es `bytes`      | Se rechaza              |
| UTF-8 inválido                 | Se rechaza              |
| Texto con acentos              | Se acepta               |

Resultado final:

```text
9 passed
```

---

# Pruebas unitarias de conexiones

El archivo `tests/test_connections.py` utiliza objetos `Mock` para probar las funciones sin iniciar conexiones TCP reales.

## Función `eliminar_cliente()`

Se verificó que:

* un cliente existente se elimine de la lista;
* el socket del cliente se cierre;
* eliminar un cliente inexistente no provoque errores.

## Función `broadcast()`

Se verificó que:

* el mensaje llegue a los demás clientes;
* el emisor no reciba su propio mensaje;
* el socket principal del servidor no reciba el mensaje;
* un cliente que falla durante el envío sea eliminado;
* el fallo de un cliente no impida enviar el mensaje al resto.

Resultado:

```text
6 passed
```

---

# Pruebas de integración

El archivo `tests/test_integration.py` ejecuta `servidor.py` como un proceso independiente y utiliza conexiones TCP reales.

El servidor se inicia antes de cada prueba y se detiene al finalizar.

Esto permite que las pruebas sean independientes entre sí.

## Distribución de mensajes

Se conectaron tres clientes:

```text
Cliente A
Cliente B
Cliente C
```

El cliente A envió un mensaje.

Se verificó que:

* B recibiera el mensaje;
* C recibiera el mensaje;
* A no recibiera su propio mensaje.

## Envíos simultáneos

Dos clientes enviaron mensajes aproximadamente al mismo tiempo.

Se comprobó que un tercer cliente:

* recibiera ambos mensajes;
* no perdiera ninguno;
* no recibiera mensajes duplicados.

## Orden de mensajes

Un mismo cliente envió dos mensajes consecutivos.

Se verificó que el receptor los recibiera en el orden esperado.

Esta garantía corresponde a mensajes enviados a través de una misma conexión TCP.

## Desconexión de clientes

Se conectaron tres clientes y uno de ellos se desconectó.

Después de la desconexión:

* los demás clientes permanecieron activos;
* los mensajes continuaron distribuyéndose;
* el proceso del servidor continuó ejecutándose.

## Mensajes inválidos

Un cliente envió un mensaje compuesto únicamente por espacios.

Se verificó que:

* el mensaje no fuera retransmitido;
* el servidor continuara funcionando.

Resultado:

```text
5 passed
```

---

# Resultado final

Se ejecutó la suite completa con:

```powershell
python -m pytest -v
```

La ejecución recopiló y aprobó las 20 pruebas:

```text
20 passed
```

Distribución:

| Tipo de prueba         | Cantidad |
| ---------------------- | -------: |
| Validación de mensajes |        9 |
| Conexiones y broadcast |        6 |
| Integración            |        5 |
| **Total**              |   **20** |

---

# Evidencias

Las salidas originales de Pytest se almacenan en la carpeta `evidencias/`.

Ejemplo para guardar una ejecución:

```powershell
python -m pytest -v |
Tee-Object -FilePath evidencias/resultado_suite_completa.txt
```

Estas evidencias conservan los resultados reales de cada etapa del proceso:

* RED inicial;
* GREEN inicial;
* segundo RED;
* validación final;
* conexiones;
* integración;
* suite completa.

---

# Decisiones técnicas

## Mantener una implementación simple

No se agregaron clases, frameworks de red ni arquitecturas adicionales.

El servidor conserva su estructura original basada en:

* una lista de sockets;
* `select.select()`;
* un ciclo principal;
* funciones auxiliares pequeñas.

## Separar responsabilidades

La refactorización permitió probar por separado:

```python
validar_mensaje()
eliminar_cliente()
broadcast()
```

Esto redujo el acoplamiento entre la lógica de negocio y el ciclo principal del servidor.

## Uso de mocks

Los mocks se utilizaron únicamente en las pruebas unitarias para simular sockets.

Las pruebas de integración utilizaron sockets TCP reales.

## Ejecución independiente

Cada prueba de integración inicia su propio proceso del servidor y lo termina al finalizar.

Esto evita que una prueba dependa del estado dejado por otra.

---

# Conclusión

La implementación final cumple los requisitos obligatorios del desafío sin modificar innecesariamente la arquitectura original del chat.

Las pruebas permitieron comprobar tanto funciones individuales como el comportamiento conjunto del servidor y los clientes.

El ciclo TDD ayudó a identificar progresivamente los comportamientos faltantes en la validación de mensajes.

El resultado final de 20 pruebas aprobadas confirma que los escenarios definidos funcionan correctamente y que el servidor puede manejar múltiples conexiones, distribución de mensajes, entradas inválidas y desconexiones sin bloquearse.
