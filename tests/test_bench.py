"""Pruebas del banco contra GuitarSet.

El banco decide si un cambio de las reglas mejora o empeora en muchas grabaciones a la vez.
Si cuenta mal, se ajustan las reglas en la dirección equivocada en todas, así que lo que
decide qué es un acierto, un invento o un armónico se prueba con notas puestas a mano.
"""

import unittest

from bench import is_overtone, match, roles, score


class Emparejar(unittest.TestCase):
    def test_acierta_la_misma_altura_dentro_del_margen(self):
        self.assertEqual(match([(1.0, 60)], [(1.08, 60)]), {0: 0})

    def test_no_acierta_fuera_del_margen_ni_con_otra_altura(self):
        self.assertEqual(match([(1.0, 60)], [(1.2, 60), (1.0, 61)]), {})

    def test_una_nota_detectada_no_acierta_dos_de_la_respuesta(self):
        # Dos Do seguidos en la respuesta y uno solo detectado: un acierto, no dos.
        self.assertEqual(len(match([(1.0, 60), (1.05, 60)], [(1.02, 60)])), 1)


class Papeles(unittest.TestCase):
    def test_melodia_arriba_bajo_abajo_y_lo_demas_interno(self):
        notas = [(0.0, 40), (0.01, 55), (0.02, 67)]
        self.assertEqual([r for _, _, r in roles(notas)], ["bajo", "int", "mel"])

    def test_ataques_separados_se_miran_por_separado(self):
        notas = [(0.0, 45), (0.5, 64)]
        self.assertEqual([r for _, _, r in roles(notas)], ["bajo", "mel"])


class Inventos(unittest.TestCase):
    def test_la_octava_de_una_nota_real_cuenta_como_armonico(self):
        self.assertTrue(is_overtone((1.0, 52), [(1.0, 40)]))

    def test_una_nota_suelta_no_es_armonico(self):
        self.assertFalse(is_overtone((1.0, 53), [(1.0, 40)]))

    def test_cuenta_inventos_y_armonicos(self):
        respuesta = [(0.0, 40), (0.0, 64)]
        detectado = [(0.0, 40), (0.0, 52), (0.0, 61)]
        r = score(respuesta, detectado)
        self.assertEqual((r["hits"], r["invented"], r["overtones"]), (1, 2, 1))
        self.assertEqual(r["roles"], {"bajo": (1, 1), "mel": (1, 0)})


if __name__ == "__main__":
    unittest.main()
