"""Pruebas de la escritura de la canción: el largo del compás y el compás escrito.

Las canciones hechas a mano son 4/4 y no deben cambiar; el borrador puede salir en 12/8, y
ahí el compás suma 24 semicorcheas en vez de 16.
"""

import json
import tempfile
import unittest
from pathlib import Path

from tabgen import Builder, write_song

META = {"title": "t", "artist": "", "tab_author": "", "source_url": "", "tempo_bpm": 90.0}


class Compas(unittest.TestCase):
    def test_un_compas_de_veinticuatro_acepta_la_redonda_con_puntillo(self):
        compas = Builder().bar([(0, "")], "mf", slots=24)

        pulso = compas["voices"][0]["beats"][0]
        self.assertEqual((pulso["duration"], pulso["dots"]), (1, 1))

    def test_un_compas_de_veinticuatro_en_dos_mitades(self):
        compas = Builder().bar([(0, "1:0::"), (12, "")], "mf", slots=24)

        figuras = [(b["duration"], b["dots"]) for b in compas["voices"][0]["beats"]]
        self.assertEqual(figuras, [(2, 1), (2, 1)])

    def test_por_defecto_el_compas_dura_dieciseis(self):
        with self.assertRaises(ValueError):
            Builder().bar([(0, ""), (4, "")], "mf", slots=24)
        Builder().bar([(0, ""), (4, "")], "mf")


class Cancion(unittest.TestCase):
    def escribir(self, **extra):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "c.json"
            write_song(
                ruta, META, 0, [("Verso", "Parte 1", 0, 1)], [([(0, "")], "mf", False)], **extra
            )
            return json.loads(ruta.read_text(encoding="utf-8"))

    def test_por_defecto_es_cuatro_cuatro(self):
        cancion = self.escribir()

        self.assertEqual(
            cancion["master_bars"][0]["time_signature"], {"numerator": 4, "denominator": 4}
        )

    def test_doce_octavos_escribe_el_compas_y_suma_veinticuatro(self):
        cancion = self.escribir(time_signature=(12, 8))

        self.assertEqual(
            cancion["master_bars"][0]["time_signature"], {"numerator": 12, "denominator": 8}
        )
        pulso = cancion["tracks"][0]["staves"][0]["bars"][0]["voices"][0]["beats"][0]
        self.assertEqual((pulso["duration"], pulso["dots"]), (1, 1), "un compás vacío de 24")


if __name__ == "__main__":
    unittest.main()
