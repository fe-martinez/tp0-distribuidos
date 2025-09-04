# Protocolo de comunicación

Todos los mensajes mantienen el encapsulamiento [header de 8 bytes + body]

* Cliente se conecta al servidor
* Cliente comienza a enviar mensajes de [batches](#protocolo-de-batches)
* Cliente procesa esos mensajes (devolviendo success o error por batch)
* Cuando el cliente termina de enviar sus apuestas, escribe END al servidor, indicando que esta listo para obtener la lista de ganadores.
* Cuando se haya terminado con todos los clientes, el servidor envía a cada uno su lista de ganadores de la forma: `dni1;dni2;dni3...;dniN` siempre delimitado por el len del header. Si no hay ganadores escribe `NO_WINNERS`.

Consideraciones: 
* Podría haberse implementado un protocolo en 2 partes donde el cliente se desconecta al terminar de mandar apuestas y se vuelve a conectar para pedir los ganadores. Como en este caso todo ocurre al mismo tiempo no es necesario. Para este caso tampoco hace falta mandar un mensaje de END y otro mensaje indicando que se estan esperando los ganadores, el primero ya implica el segundo.


# Protocolo de batches

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