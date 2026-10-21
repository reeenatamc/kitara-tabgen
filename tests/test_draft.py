"""Pruebas del pulgar escrito.

El pulgar escrito es lo que más bajos fantasma metía: borraba el grave detectado y lo
reescribía con el acorde adivinado. Ahora sólo rellena, y sólo si el acorde se confirma en
el grave; estas pruebas fijan las dos condiciones.
"""

import unittest

from tabgen import Builder
from transcriber.draft import bar_events, harmonize, metadata
from transcriber.music import COMPOUND, SIMPLE

# Si menor: fundamental Si (47 en la quinta cuerda), quinta Fa# (42 en la sexta).
SI = 47
FA_SOSTENIDO = 42
RE_AGUDO = 62


class Pulgar(unittest.TestCase):
    def test_conserva_el_bajo_que_se_oyo(self):
        # Un bajo en el segundo tiempo no es del pulgar alternado, pero sonó: se queda.
        oido = {0: {SI: 0.8, RE_AGUDO: 0.7}, 4: {45: 0.6}}

        escrito = harmonize(oido, [0], ["Sim"], SIMPLE)

        self.assertIn(45, escrito[4])
        self.assertIn(SI, escrito[0])

    def test_rellena_el_tercer_tiempo_si_falta_bajo(self):
        oido = {0: {SI: 0.8}, 8: {RE_AGUDO: 0.7}}

        escrito = harmonize(oido, [0], ["Sim"], SIMPLE)

        self.assertIn(FA_SOSTENIDO, escrito[8])
        self.assertIn(RE_AGUDO, escrito[8], "la melodía de ese tiempo sigue ahí")

    def test_no_pisa_un_bajo_distinto_que_si_sono(self):
        oido = {0: {SI: 0.8}, 8: {45: 0.6}}

        escrito = harmonize(oido, [0], ["Sim"], SIMPLE)

        self.assertEqual(set(escrito[8]), {45})

    def test_no_escribe_nada_si_el_grave_no_confirma_el_acorde(self):
        # El acorde adivinado dice Si menor, pero en el grave sólo sonó un La.
        oido = {0: {45: 0.8}, 4: {RE_AGUDO: 0.7}}

        escrito = harmonize(oido, [0], ["Sim"], SIMPLE)

        self.assertEqual(escrito, oido)

    def test_sin_acorde_deja_todo_como_se_oyo(self):
        oido = {0: {SI: 0.8}, 4: {RE_AGUDO: 0.7}}

        self.assertEqual(harmonize(oido, [0], [None], SIMPLE), oido)

    def test_en_compuesto_los_tiempos_fuertes_son_cero_y_doce(self):
        oido = {0: {SI: 0.8}, 12: {RE_AGUDO: 0.7}}

        escrito = harmonize(oido, [0], ["Sim"], COMPOUND)

        self.assertIn(FA_SOSTENIDO, escrito[12])
        self.assertNotIn(8, escrito, "el tiempo fuerte de 4/4 ya no cuenta")


class Compases(unittest.TestCase):
    def test_un_compas_de_veinticuatro_se_reparte_en_figuras_que_existen(self):
        colocado = {0: (((5, 2),), 0), 6: (((1, 0),), 0)}

        eventos = bar_events(colocado, 0, COMPOUND)

        # Del segundo ataque al final quedan 18: una redonda sin puntillo y lo que sobra.
        self.assertEqual([pos for pos, _ in eventos], [0, 6, 22])
        Builder().bar(eventos, "mf", slots=24)

    def test_dos_pulsos_en_compuesto_son_dos_negras_con_puntillo_ligadas_a_nada(self):
        colocado = {0: (((5, 2),), 0), 12: (((1, 0),), 0)}

        self.assertEqual([pos for pos, _ in bar_events(colocado, 0, COMPOUND)], [0, 12])

    def test_un_compas_vacio_es_una_redonda_con_puntillo(self):
        self.assertEqual(bar_events({}, 24, COMPOUND), [(0, "")])

    def test_el_tempo_va_en_negras(self):
        self.assertEqual(metadata("x", 80.0, SIMPLE)["tempo_bpm"], 80.0)
        self.assertEqual(metadata("x", 80.0, COMPOUND)["tempo_bpm"], 120.0)


if __name__ == "__main__":
    unittest.main()
