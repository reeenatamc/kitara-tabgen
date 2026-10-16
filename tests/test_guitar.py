"""Pruebas del mapeo a la guitarra.

La parte con más lógica del transcriptor: una nota se puede pisar en varios sitios y lo que
decide es la secuencia entera, no cada nota suelta. Eso es lo que estas pruebas vigilan.
"""

import unittest

from transcriber.guitar import (
    MAX_FRET,
    TUNING,
    fit_range,
    hand_position,
    notation,
    place,
    voicing_cost,
    voicings,
)


def altura(cuerda, traste):
    """La altura MIDI que da pisar una cuerda en un traste."""
    return TUNING[cuerda - 1] + traste


class CaberEnElMastil(unittest.TestCase):
    def test_sube_por_octavas_lo_que_queda_grave(self):
        # Por debajo de la sexta al aire no hay nada que pisar.
        grave = TUNING[-1] - 5

        self.assertEqual(fit_range(grave), grave + 12)

    def test_baja_por_octavas_lo_que_queda_agudo(self):
        agudo = TUNING[0] + MAX_FRET + 3

        self.assertEqual(fit_range(agudo), agudo - 12)

    def test_deja_en_paz_lo_que_ya_cabe(self):
        self.assertEqual(fit_range(TUNING[0]), TUNING[0])


class Posturas(unittest.TestCase):
    def test_una_nota_sale_en_todas_las_cuerdas_donde_cabe(self):
        # Un mi agudo se pisa al aire en la primera y también en la segunda y la tercera.
        encontradas = voicings([64])

        cuerdas = sorted(combo[0][0] for combo in encontradas)
        self.assertEqual(cuerdas, [1, 2, 3, 4])

    def test_no_pone_dos_notas_en_la_misma_cuerda(self):
        for combo in voicings([50, 62]):
            cuerdas = [cuerda for cuerda, _ in combo]
            self.assertEqual(len(cuerdas), len(set(cuerdas)))

    def test_descarta_lo_que_no_alcanza_la_mano(self):
        # Pisar el traste 10 y el 3 a la vez son siete trastes de abertura.
        for combo in voicings([50, 62]):
            pisados = [traste for _, traste in combo if traste > 0]
            if pisados:
                self.assertLessEqual(max(pisados) - min(pisados), 3)

    def test_una_altura_imposible_no_da_posturas(self):
        self.assertEqual(voicings([TUNING[0] + MAX_FRET + 1]), [])


class ManoYCoste(unittest.TestCase):
    def test_un_acorde_al_aire_deja_la_mano_donde_estaba(self):
        self.assertEqual(hand_position(((1, 0), (2, 0)), 7), 7)

    def test_la_mano_va_al_traste_mas_bajo_que_se_pisa(self):
        self.assertEqual(hand_position(((1, 5), (2, 7)), 0), 5)

    def test_al_aire_no_cuesta_nada(self):
        self.assertEqual(voicing_cost(((1, 0), (2, 0))), 0.0)

    def test_abrir_la_mano_cuesta_mas_que_no_abrirla(self):
        self.assertGreater(voicing_cost(((1, 5), (2, 8))), voicing_cost(((1, 5), (2, 5))))

    def test_subir_por_el_mastil_cuesta_un_poco(self):
        self.assertGreater(voicing_cost(((1, 12),)), voicing_cost(((1, 2),)))


class Colocar(unittest.TestCase):
    def test_evita_el_salto_aunque_la_primera_postura_salga_mas_cara(self):
        # Un mi agudo y luego el mi una octava arriba, que sólo se pisa en el traste 12.
        #
        # Nota a nota, lo barato para el primero es la primera cuerda al aire: no cuesta
        # nada. Pero deja la mano en el traste 0 y obliga a un salto de doce. Mirando los dos
        # juntos sale más barato pisar el primero arriba y quedarse cerca.
        #
        # Si esto se rompe, el borrador sale con la mano saltando por todo el mástil y no
        # hay nada que corregir de oído, hay que rehacer la digitación.
        colocado = place({0: {64: 1.0}, 1: {76: 1.0}})

        primera, _ = colocado[0]
        self.assertNotEqual(
            primera[0],
            (1, 0),
            "eligió la cuerda al aire y se queda a doce trastes de la siguiente",
        )

        segunda, _ = colocado[1]
        salto = abs(hand_position(primera, 0) - hand_position(segunda, 0))
        self.assertLessEqual(salto, 3, "la mano se mueve poco, salió un salto de %d" % salto)

    def test_una_sola_posicion_tambien_se_coloca(self):
        colocado = place({0: {64: 1.0}})

        self.assertEqual(len(colocado), 1)
        combo, _ = colocado[0]
        self.assertEqual(altura(*combo[0]), 64)

    def test_cada_posicion_suena_a_la_altura_que_se_detecto(self):
        slots = {0: {40: 1.0, 64: 1.0}, 4: {45: 1.0}, 8: {62: 1.0}}

        colocado = place(slots)

        for slot, (combo, _) in colocado.items():
            sonando = sorted(altura(cuerda, traste) for cuerda, traste in combo)
            pedidas = sorted(fit_range(p) for p in slots[slot])
            self.assertEqual(sonando, pedidas, "el compás %d no suena a lo detectado" % slot)

    def test_conserva_el_orden_de_las_posiciones(self):
        colocado = place({8: {64: 1.0}, 0: {62: 1.0}, 4: {60: 1.0}})

        self.assertEqual(sorted(colocado), [0, 4, 8])


class Notacion(unittest.TestCase):
    def test_el_dedo_sale_de_la_distancia_a_la_mano(self):
        # Con la mano en el traste 5: el índice pisa el 5, el medio el 6, el anular el 7.
        texto = notation(((1, 5), (2, 6), (3, 7)), 5, None)

        self.assertEqual(texto, "1:5:I: 2:6:M: 3:7:A:")

    def test_una_cuerda_al_aire_no_lleva_dedo(self):
        self.assertEqual(notation(((6, 0),), 0, None), "6:0::")

    def test_la_cuerda_de_la_melodia_lleva_acento(self):
        texto = notation(((1, 7), (4, 5)), 5, 1)

        self.assertIn("1:7:A:a", texto, "la primera lleva el acento")
        self.assertIn("4:5:I:", texto)


if __name__ == "__main__":
    unittest.main()
