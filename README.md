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