<!-- Qué estaba mal, qué hace ahora y cómo se comprobó. En prosa, sin listas de una línea. -->

Closes #

**Probado:** `.venv/bin/python -m unittest discover -s tests -t .` y la salida del
transcriptor comparada contra la de antes (tiene que dar el mismo JSON salvo el UUID).
