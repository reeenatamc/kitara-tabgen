"""Borrador de tablatura desde audio, por piezas.

- `signal`: lo que se oye, con basic-pitch y librosa. Es la única parte con dependencias
  pesadas.
- `music`: qué suena en cada semicorchea, dónde empiezan los compases y qué acorde es cada
  uno.
- `guitar`: en qué cuerda y traste se pisa cada cosa, moviendo la mano lo menos posible.
- `draft`: el JSON de la canción y su guía.

Todo menos `signal` son funciones sin estado y sin dependencias del sistema, para poder
probarlas con notas puestas a mano.
"""
