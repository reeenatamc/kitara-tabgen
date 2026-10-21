"""Pruebas del vocabulario de ritmos.

Lo que hay que sujetar aquí es que puntuar un compás contra el vocabulario distinga de
verdad, porque de eso depende la eleccion del nivel metrico, y equivocarse ahi no da un
borrador peor: da uno con los compases en otro sitio, que no se puede corregir de oido.
"""

import unittest
from collections import Counter

import vocabulary

#: Corcheas seguidas, que es el molde que cubre 91 de los 199 compases escritos a mano.
EIGHTHS = (0, 2, 4, 6, 8, 10, 12, 14)

#: Semicorcheas seguidas: lo que sale si el tempo se lee a la mitad del que es.
SIXTEENTHS = tuple(range(16))


class LeerElRitmoDeUnaPartitura(unittest.TestCase):
    def _score(self, beats):
        return {"tracks": [{"staves": [{"bars": [{"voices": [{"beats": beats}]}]}]}]}

    def test_cuatro_negras_atacan_en_los_tiempos(self):
        beats = [{"duration": 4, "notes": [{"string": 1, "fret": 0}]} for _ in range(4)]
        self.assertEqual(vocabulary.bar_shapes(self._score(beats)), [(0, 4, 8, 12)])

    def test_una_nota_ligada_no_es_un_ataque(self):
        """Una ligadura suena pero no se pulsa, y el molde es de pulsaciones."""
        beats = [
            {"duration": 4, "notes": [{"string": 1, "fret": 0}]},
            {"duration": 4, "notes": [{"string": 1, "fret": 0, "tie_destination": True}]},
            {"duration": 4, "notes": [{"string": 1, "fret": 0}]},
            {"duration": 4, "notes": [{"string": 1, "fret": 0}]},
        ]
        self.assertEqual(vocabulary.bar_shapes(self._score(beats)), [(0, 8, 12)])

    def test_un_silencio_no_ocupa_posicion_pero_si_avanza(self):
        beats = [
            {"duration": 4, "notes": []},
            {"duration": 4, "notes": [{"string": 1, "fret": 0}]},
        ]
        self.assertEqual(vocabulary.bar_shapes(self._score(beats)), [(4,)])

    def test_un_puntillo_alarga_la_figura(self):
        beats = [
            {"duration": 4, "dots": 1, "notes": [{"string": 1, "fret": 0}]},
            {"duration": 8, "notes": [{"string": 1, "fret": 0}]},
        ]
        self.assertEqual(vocabulary.bar_shapes(self._score(beats)), [(0, 6)])

    def test_un_compas_vacio_no_entra(self):
        beats = [{"duration": 1, "notes": []}]
        self.assertEqual(vocabulary.bar_shapes(self._score(beats)), [])


class ArmarElVocabulario(unittest.TestCase):
    def test_un_molde_que_aparece_una_sola_vez_no_es_un_patron(self):
        """Si entrara, el vocabulario sería la lista de compases y no distinguiría nada."""
        counter = Counter({EIGHTHS: 5, (0, 1, 2): 1})
        kept = Counter({s: n for s, n in counter.items() if n >= vocabulary.MIN_TIMES})
        self.assertIn(EIGHTHS, kept)
        self.assertNotIn((0, 1, 2), kept)


class PuntuarUnCompas(unittest.TestCase):
    def setUp(self):
        self.vocabulary = Counter({EIGHTHS: 91, (0, 4, 8, 12): 12})

    def test_el_molde_exacto_puntua_mas_que_otro(self):
        exacto = vocabulary.fit(EIGHTHS, self.vocabulary)
        otro = vocabulary.fit((0, 1, 3, 5, 7, 9, 11, 13), self.vocabulary)
        self.assertGreater(exacto, otro)

    def test_un_compas_sin_ataques_no_puntua(self):
        self.assertEqual(vocabulary.fit((), self.vocabulary), 0.0)

    def test_sin_vocabulario_no_se_puede_puntuar(self):
        self.assertEqual(vocabulary.fit(EIGHTHS, Counter()), 0.0)

    def test_tener_mas_ataques_no_hace_ganar_por_si_solo(self):
        """Por eso se divide por la unión: si no, las semicorcheas seguidas ganarían siempre."""
        self.assertGreater(
            vocabulary.fit(EIGHTHS, self.vocabulary),
            vocabulary.fit(SIXTEENTHS, self.vocabulary),
        )

    def test_parecerse_al_molde_comun_vale_mas_que_a_uno_raro(self):
        comun = Counter({EIGHTHS: 91, (0, 4, 8, 12): 2})
        self.assertGreater(
            vocabulary.fit(EIGHTHS, comun),
            vocabulary.fit((0, 4, 8, 12), comun),
        )


class ElegirElNivelMetrico(unittest.TestCase):
    def setUp(self):
        self.vocabulary = Counter({EIGHTHS: 91})

    def test_con_corcheas_a_un_segundo_el_pulso_es_de_un_segundo(self):
        """Ocho ataques por compás a 0,5 s: el compás dura 4 s, o sea negra de 1 s."""
        onsets = [bar * 4.0 + slot * 0.5 for bar in range(12) for slot in range(8)]
        period, _, score = vocabulary.choose_level(onsets, 0.0, 1.0, 48.0, self.vocabulary)
        self.assertAlmostEqual(period, 1.0, places=2)
        self.assertGreater(score, 0.8)

    def test_el_periodo_al_doble_se_corrige(self):
        """Es el fallo real: salvatore va a 60 y el detector dice 117."""
        onsets = [bar * 4.0 + slot * 0.5 for bar in range(12) for slot in range(8)]
        period, _, _ = vocabulary.choose_level(onsets, 0.0, 0.5, 48.0, self.vocabulary)
        self.assertAlmostEqual(period, 1.0, places=2)

    def test_una_grabacion_demasiado_corta_no_decide_nada(self):
        """Con menos de cuatro compases no hay con qué comparar, y vale más no tocar nada."""
        period, shift, score = vocabulary.choose_level([0.1, 0.6], 0.0, 1.0, 2.0, self.vocabulary)
        self.assertEqual((period, shift, score), (1.0, 0, 0.0))
