1. Describa la arquitectura Cliente-Servidor.

En esta arquitectura los clientes asumen que existe una computadora (servidor) escuchando en una dirección IP + puerto específico lista para resolver pedidos de los clientes y responder siguiendo algún tipo de protocolo de comunicación previamente establecido.

A diferencia de la arquitectura P2P en la que no existe un servidor dedicado con este proposito sino que los clientes pueden o no tomar este rol en ciertos escenarios de comunicacion entre ellos.

2. ¿Cuál es la función de un protocolo de capa de aplicación?

Permite definir las reglas de como se va a llevar a cabo la comunicacion entre 2 aplicaciones. Por ejemplo especifica el formato que llevan los datos.

3. Detalle el protocolo de aplicación desarrollado en este trabajo.

Partimos el protocolo en dos partes, una simula ser un protocolo de capa de transporte el cual utiliza UDP e implementa la transferencia de datos confiable. La otra parte vive por encima de esta y utiliza su interfaz para implementar un servicio de transferencia de archivos confiable.

No queriamos juntar todo en un solo lugar porque pensamos que podría complejizar mucho las cosas tener todo mezclado. De esta forma las aplicaciones podrían cambiar la implementación del socket que utilizan por uno con TCP y no debería haber ningún problema.

4. La capa de transporte del stack TCP/IP ofrece dos protocolos: TCP y UDP. ¿Qué servicios proveen dichos protocolos? ¿Cuáles son sus características? ¿Cuando es apropiado utilizar cada uno?

UDP brinda 2 servicios.
- Multiplexación y Demultiplexación
- Integridad de datagramas

TCP brinda 6 servicios.
- Multiplexación y Demultiplexación
- Integridad de segmentos
- Fiabilidad
- Orden de segmentos
- Control de flujo
- Control de conjestión

Multiplexación y Demultiplexación: Es el modo de diferenciar de que proceso es cada segmento, por ejemplo juntar los distintos segmentos de varios procesos que tienen que salir por el mismo cable y luego al momento de recibir segmentos poder diferenciar de quien es cada uno.

Integridad de segmentos: Ambos servicios implementan un sistema de checksum que se aplica sobre el header y los datos para garantizar (o por lo menos tener una baja probabilidad) de que los datos no hayan sido corrompidos durante el traslado del segmento por la red.

Fiabilidad: Los datos que se envian podemos garantizar que llegan al otro proceso.

Orden de segmentos: La información llega en el mismo orden en el que se envía.

Control de flujo: Es el control de la taza de envío de los segmentos para no desaprovechar ancho de banda pero a la vez no abrumar al otro proceso receptor de nuestros segmentos.

Control de conjestión: Es un sistema que permite regular la velocidad de envío teniendo un cuidado más panoramico donde suponemos que si estamos perdiendo segmentos entonces es porque la red está saturada. Esto funciona porque muchas aplicaciones deciden utilizar TCP como protocolo de capa de transporte y al auto regularse intenta proteger a la red de que no caiga en un estado inutilizable donde segmento que se envie se pierda.

UDP es un buen protocolo en situaciones donde la velocidad de transferencia es clave y no nos importa tanto que se pierdan datagramas, de ser así podriamos implementar un protocolo de aplicación que brinde este servicio y no los demás que brinda TCP (como en este trabajo práctico).

TCP brilla en ser completo. Brinda casi todas las comodidades que pueda tener un protocolo de transporte, no brinda por ejemplo encriptación de datos. Lo más destacable siendo la fiabilidad y orden de segmentos, la información va a llegar en el orden esperado, el control de flujo ayuda a mantener buen performance sin abrumar la cola de segmentos del otro lado y el control de conjestión es un servicio que se brinda a toda la red.

Siendo que ambos protocolos implementan integridad de segmentos, no es algo que sea una ventaja para ninguno. En cuanto a multiplexación y demultiplexación, es el mínimo indispensable para ser considerado un protocolo de transporte. De otra manera no podríamos determinar a que proceso entregar un datagrama/segmento recién recibido de la capa de red.
