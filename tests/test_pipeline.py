"""Prueba del recorrido de reglas.

`transcribe.py` y `bench.py` usan este recorrido, así que lo que se mide es lo que se
entrega. Aquí sólo se fija que las etapas encadenen: lo que hace cada regla se prueba en su
propio archivo.
"""

import unittest
from itertools import pairwise

from transcriber.music import COMPOUND, SIMPLE
from transcriber.pipeline import run


def nota(inicio, altura, amp=0.8):
    return (inicio, inicio + 0.2, altura, amp)


class Recorrido(unittest.TestCase):
    def test_encadena_las_etapas(self):
        # Dos compases de Si menor: bajo Si2 en cada tiempo y una melodía arriba.
        pulsos = [i * 0.5 for i in range(10)]
        notas = [nota(t * 0.5, 47) for t in range(8)] + [nota(0.25, 66), nota(1.25, 69)]

        etapas = run(notas, pulsos, 0.5)

        self.assertEqual(etapas.meter, SIMPLE)
        self.assertEqual(len(etapas.grid), 36, "nueve huecos de cuatro semicorcheas")
        self.assertEqual(len(etapas.cleaned), len(notas), "no hay nada que limpiar")
        self.assertEqual(len(etapas.starts), len(etapas.chords))
        alturas = {p for voces in etapas.slots.values() for p in voces}
        self.assertTrue({47, 66, 69} <= alturas, "el bajo y la melodía llegan al final")

    def test_unas_corcheas_de_tresillo_arman_un_compas_de_veinticuatro(self):
        # Tres notas por pulso, la primera grave: compuesto, y compases de 24 semicorcheas.
        pulsos = [float(i) for i in range(14)]
        notas = [
            nota(i + fase, 47 if fase == 0 else 66) for i in range(12) for fase in (0, 1 / 3, 2 / 3)
        ]

        etapas = run(notas, pulsos, 1.0)

        self.assertEqual(etapas.meter, COMPOUND)
        self.assertEqual(len(etapas.grid), 78, "trece huecos de seis semicorcheas")
        self.assertTrue(all(b - a == 24 for a, b in pairwise(etapas.starts)))


if __name__ == "__main__":
    unittest.main()
