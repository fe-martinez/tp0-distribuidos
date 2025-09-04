# Ejercicio 4

Para implementar _graceful shutdowns_ al recibir señales SIGTERM o SIGINT, utilizamos los mecanismos nativos que provee cada lenguaje:

En Python, usamos el módulo signal para registrar una función handler personalizada. Esta función reemplaza el comportamiento por defecto y se ejecuta al recibir la señal, permitiéndonos iniciar un cierre controlado de la aplicación.

En Go, aprovechamos el paquete os/signal en conjunto con los canales. Configuramos un canal para que reciba las notificaciones de las señales y una gorutina independiente se bloquea a la espera de un mensaje. Al recibir la señal en el canal, se activa la lógica de apagado.

# Ejercicio 3

En este ejercicio es necesario levantar un container de docker temporal que se encargue de enviar un mensaje de prueba al servidor.

El script es bastante descriptivo en este caso, se hace docker run --rm para que en el momento que el unico proceso que se ejecuta termine, el container sea borrado.

Se opto por busybox porque es una imagen pequeña que permite correr netcat de manera muy simple

# Ejercicio 2

Para lograr lo que pide este ejercicio se hicieron 3 cambios:
* Agregar la declaración de un volume al script que genera el archivo de docker compose.
* Remover el COPY al archivo de configuración en el Dockerfile del cliente y del servidor.
* Agregar a .dockerignore los archivos de configuración para que no sean copiados a la imagen.

# Ejercicio 1

Arme el script mas simple que pude, usando solo bash. Como solo es concatenar strings estaticos en un file me parecio la opción correcta.

Para ejecutarlo de 0

```
chmod +x generar-compose.sh
./generar-compose-sh <path> <cantidad-clientes>
```

El script tiene una ruta default que es la que se usa para levantar los containers con el makefile por simplicidad. También tiene una cantidad default de clientes por si no se envia nada.
