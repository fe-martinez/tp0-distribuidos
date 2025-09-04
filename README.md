# Ejercicio 8: Concurrencia

### Modelo de concurrencia

Listener/Worker con multithreading:
El proceso principal acepta conexiones y para cada cliente lanza un thread worker dedicado. Esto permite efectivamente procesar varios clientes a la vez.
Aunque existe el GIL, el caso es I/O-bound (sockets y archivo CSV) y no cpu-intensivo por lo que los threads se solapan en espera de las operaciones de entrada/salida.
Se podrían haber usado procesos para tener paralelismo pero en este caso no era algo necesario por las condiciones del problema.

Barrier:
Cada cliente envía sus batches y, al finalizar, notifica con un mensaje END. Al recibirlo, su hilo llega a la barrera y espera a que lleguen las 5 agencias. Se tomo este
acercamiento por simplicidad, el protocolo define que el servidor debe esperar a que las 5 agencias notifiquen que terminaron de enviar las apuestas. Como sabemos que se
conectan todos al mismo tiempo no hay necesidad de que las agencias esten consultando varias veces si el servidor ya esta listo para enviar las apuestas. Solo una vez que
todos los threads llegaron a notificar, se hace el sorteo y se envian los ganadores.

Mutex:
Como store_bets(...) no es thread-safe, se opto por usar un mutex para que cada thread pueda acceder a ella. En el caso de load_bets(...) al estar dentro de la función
que se triggerea cuando todos los threads llegaron a la barrier, no es necesario usar el mutex.