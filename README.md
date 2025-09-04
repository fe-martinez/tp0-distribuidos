# Ejercicio 8: Modelo de concurrencia

**Listener/Worker con multithreading**:
* El proceso principal acepta conexiones y para cada cliente lanza un thread worker dedicado. Esto permite que efectivamente procesemos varios clientes a la vez.
* Aunque existe el GIL, el caso es I/O-bound (sockets y archivso CSV) y no cpu-intensivo por lo que los threads van a estar gran parte del tiempo esperando operaciones de entrada/salida, dejando la posibilidad de ejecutarse a los demas.
* Se podrían haber usado procesos para tener paralelismo pero en este caso no era algo necesario por las condiciones del problema.
* Una vez que se aceptaron los N threads (parametro que viene definido en las variables de entorno) el hilo principal procede a esperarlos con un join.

**Barrier**:
Cada cliente envía sus batches y, al finalizar, notifica con un mensaje END. Al recibirlo, su hilo llega a la barrera y espera a que lleguen las N agencias. Se tomo este acercamiento por simplicidad, el protocolo define que el servidor debe esperar a que las N agencias notifiquen que terminaron de enviar las apuestas. Como sabemos que se conectan todos al mismo tiempo no hay necesidad de que las agencias esten consultando varias veces si el servidor ya esta listo para enviar las apuestas. Solo una vez que todos los threads llegaron a notificar, se hace el sorteo y se envian los ganadores.

**Mutex**:
Como store_bets(...) no es thread-safe, se opto por usar un mutex para que cada thread pueda acceder a ella. En el caso de load_bets(...) al estar dentro de la función
que se triggerea cuando todos los threads llegaron a la barrier, no es necesario usar el mutex.

# Ejercicio 7: Protocolo de comunicación

Todos los mensajes mantienen el encapsulamiento [header de 8 bytes + body]

* Cliente se conecta al servidor
* Cliente comienza a enviar mensajes de [batches](#protocolo-de-batches)
* Cliente procesa esos mensajes (devolviendo success o error por batch)
* Cuando el cliente termina de enviar sus apuestas, escribe END al servidor, indicando que esta listo para obtener la lista de ganadores.
* Cuando se haya terminado con todos los clientes, el servidor envía a cada uno su lista de ganadores de la forma: `dni1;dni2;dni3...;dniN` siempre delimitado por el len del header. Si no hay ganadores escribe `NO_WINNERS`.

Consideraciones: 
* Podría haberse implementado un protocolo en 2 partes donde el cliente se desconecta al terminar de mandar apuestas y se vuelve a conectar para pedir los ganadores. Como en este caso todo ocurre al mismo tiempo no es necesario. Para este caso tampoco hace falta mandar un mensaje de END y otro mensaje indicando que se estan esperando los ganadores, el primero ya implica el segundo.

# Ejercicio 6: Protocolo de batches

* Para este ejercicio reemplazamos el formato anterior que enviaba una unica apuesta.
* Los mensajes se encapsulan, primero en un mensaje vienen exactamente 8 bytes que definen el largo del payload.
* len(payload) termina siendo exactamente ese largo.
* Los campos estan separados por ;
* Un batch de apuestas tiene este aspecto:

```
    <agency_id>;<cantidad_apuestas>\n 
    <nombre>;<apellido>;<dni>;<yyyy-mm-dd>;<numero>\n
    <nombre>;<apellido>;<dni>;<yyyy-mm-dd>;<numero>\n
    ...
    <nombre>;<apellido>;<dni>;<yyyy-mm-dd>;<numero>\n
```

Ante un batch, el servidor puede responder:

`success;Batch stored successfully.` y logear action: `apuesta_recibida | result: success | cantidad: {N}`

o bien responder:

`error;<mensaje_de_error>` y logear action: `action: apuesta_recibida | result: fail | cantidad: {N|0}`

El servidor solo responde “success” si todas las apuestas del batch fueron correctas.

# Ejercicio 5

Definimos un protocolo simple para enviar una unica apuesta. Este es:

`idAgencia;nombre;apellido;dni;fechaDeNacimiento;numeroApostado\n`

Y el servidor responde con un mensaje que puede ser de exito `status: success;message: Bet stored succesfully` O de error `status: error;message: {errMsg}`

Se envia un unico mensaje desde el cliente al servidor que esta en loop aceptando nuevas conexiones. Aunque por caracteristicas de como esta definido el ejercicio no puede suceder, ya se manejan las lecturas y escrituras para que no haya _short read_ o _short write_

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