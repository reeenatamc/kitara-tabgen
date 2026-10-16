"""Pruebas de las decisiones musicales.

Con notas puestas a mano: aquí no se carga ningún modelo ni se abre ningún audio. Son las
decisiones que más se equivocan del transcriptor, así que son las que hay que poder
comprobar.
"""

import unittest

from transcriber.music import (
    bar_phase,
    bar_starts,
    chord_name,
    clean,
    nearest_slot,
    quantize,
    subdivide,
)


def nota(inicio, altura, amp=1.0, fin=None):
    """Una nota detectada: `(inicio, fin, altura MIDI, amplitud)`."""
    return (inicio, fin if fin is not None else inicio + 0.2, altura, amp)


class Limpiar(unittest.TestCase):
    def test_tira_las_notas_flojas(self):
        notas = [nota(0.0, 60, amp=0.9), nota(0.5, 62, amp=0.1)]

        self.assertEqual([n[2] for n in clean(notas)], [60])

    def test_tira_el_ataque_doble_que_inventa_el_detector(self):
        # Dos ataques de la misma altura a 20 ms: en una cuerda eso no se toca.
        notas = [nota(0.0, 60, amp=0.9), nota(0.02, 60, amp=0.5)]

        self.assertEqual(len(clean(notas)), 1)

    def test_una_nota_repetida_sobre_la_que_sigue_sonando_se_conserva(self):
        # El fallo más caro que tuvo el transcriptor. Una nota de guitarra suena hasta que
        # entra la siguiente, así que el detector la da por larga. Si el filtro mira el
        # final de la anterior en vez de su principio, un pedal repetido cada pulso se tira
        # entero: eran 232 ataques buenos de 793.
        notas = [nota(0.0, 76, amp=0.64, fin=0.534), nota(0.534, 76, amp=0.69)]

        self.assertEqual(len(clean(notas)), 2, "medio segundo después es otra nota")

    def test_conserva_el_reataque_si_suena_mas_fuerte(self):
        notas = [nota(0.0, 60, amp=0.5, fin=1.0), nota(0.02, 60, amp=0.9)]

        self.assertEqual(len(clean(notas)), 2)

    def test_la_misma_altura_mas_tarde_es_otra_nota(self):
        notas = [nota(0.0, 60, amp=0.9, fin=0.2), nota(2.0, 60, amp=0.9)]

        self.assertEqual(len(clean(notas)), 2)


class Cuadricula(unittest.TestCase):
    def test_cada_nota_cae_en_la_semicorchea_mas_cercana(self):
        rejilla = [0.0, 0.25, 0.5, 0.75]

        self.assertEqual(nearest_slot(rejilla, 0.26), 1)
        self.assertEqual(nearest_slot(rejilla, 0.74), 3)

    def test_en_un_empate_gana_la_primera(self):
        self.assertEqual(nearest_slot([0.0, 1.0], 0.5), 0)


class Subdividir(unittest.TestCase):
    def test_un_hueco_de_un_pulso_da_cuatro_semicorcheas(self):
        self.assertEqual(subdivide(1.0, 1.0), 4)

    def test_un_golpe_saltado_da_ocho(self):
        # Si el detector se deja un golpe, el hueco vale dos pulsos: ocho semicorcheas.
        self.assertEqual(subdivide(2.0, 1.0), 8)

    def test_dos_golpes_saltados_dan_doce(self):
        self.assertEqual(subdivide(3.0, 1.0), 12)

    def test_el_vaiven_del_tempo_no_mueve_la_rejilla(self):
        # Un hueco de pulso y cuarto es el mismo pulso tocado con holgura, no una
        # semicorchea más. Tratarlo como semicorchea extra corría el resto de la pieza y
        # bajaba el acierto de «Solamente uno» del 52 % al 44 %.
        self.assertEqual(subdivide(1.25, 1.0), 4)
        self.assertEqual(subdivide(0.8, 1.0), 4)

    def test_un_hueco_de_pulso_y_medio_se_redondea_a_dos(self):
        # A partir de la mitad ya se parece más a un golpe saltado que a holgura.
        self.assertEqual(subdivide(1.6, 1.0), 8)

    def test_nunca_devuelve_menos_de_un_pulso(self):
        self.assertEqual(subdivide(0.01, 1.0), 4)

    def test_un_periodo_invalido_no_revienta(self):
        self.assertEqual(subdivide(0.5, 0.0), 4)


class Cuantizar(unittest.TestCase):
    rejilla = [0.0, 0.25, 0.5, 0.75]

    def test_guarda_la_melodia_y_el_bajo(self):
        # Alturas que no son octava unas de otras, para que no entre el filtro de armónicos.
        notas = [nota(0.0, 40), nota(0.0, 57), nota(0.0, 62)]

        slots = quantize(notas, self.rejilla, inner_voices=0)

        self.assertEqual(sorted(slots[0]), [40, 62], "la voz interna se descarta")

    def test_guarda_tambien_la_voz_interna_mas_fuerte(self):
        notas = [nota(0.0, 40), nota(0.0, 55, amp=0.4), nota(0.0, 57, amp=0.9), nota(0.0, 62)]

        slots = quantize(notas, self.rejilla, inner_voices=1)

        self.assertEqual(sorted(slots[0]), [40, 57, 62], "se queda la interna más fuerte")

    def test_tira_el_armonico_de_una_nota_mas_fuerte(self):
        # Una octava por encima de algo más fuerte casi siempre es su armónico, no una nota.
        notas = [nota(0.0, 40, amp=0.9), nota(0.0, 52, amp=0.3)]

        slots = quantize(notas, self.rejilla, inner_voices=0)

        self.assertEqual(sorted(slots[0]), [40])

    def test_tira_tambien_la_octava_de_la_octava(self):
        # El filtro mira doce, diecinueve y veinticuatro semitonos: dos octavas también.
        notas = [nota(0.0, 40, amp=1.0), nota(0.0, 64, amp=0.5)]

        slots = quantize(notas, self.rejilla, inner_voices=0)

        self.assertEqual(sorted(slots[0]), [40], "dos octavas arriba sigue siendo armónico")

    def test_conserva_la_octava_si_suena_mas_fuerte_que_la_de_abajo(self):
        notas = [nota(0.0, 40, amp=0.2), nota(0.0, 52, amp=0.9)]

        slots = quantize(notas, self.rejilla, inner_voices=0)

        self.assertEqual(sorted(slots[0]), [40, 52])


class BarrasDeCompas(unittest.TestCase):
    def test_el_compas_empieza_donde_caen_los_bajos(self):
        # Bajos en 4 y 12: el compás empieza en 4, no en 0.
        slots = {4: {40: 1.0}, 8: {64: 1.0}, 12: {40: 1.0}, 20: {40: 1.0}}

        self.assertEqual(bar_phase(slots), 4)

    def test_sin_bajos_no_revienta(self):
        slots = {0: {64: 1.0}, 5: {65: 1.0}}

        self.assertIn(bar_phase(slots), (0, 4, 8, 12))

    def test_los_compases_cubren_todo_lo_que_suena(self):
        slots = {5: {60: 1.0}, 40: {60: 1.0}}

        starts = bar_starts(slots, 4)

        self.assertEqual(starts[0], 4, "empieza en la fase y antes de la primera nota")
        self.assertGreaterEqual(starts[-1] + 16, 40, "y llega hasta la última")
        self.assertTrue(all((s - 4) % 16 == 0 for s in starts))


class Acordes(unittest.TestCase):
    def test_reconoce_un_acorde_mayor(self):
        # Do mayor: do, mi, sol.
        slots = {0: {60: 1.0, 64: 1.0, 67: 1.0}}

        self.assertEqual(chord_name(slots, 0), "Do")

    def test_reconoce_un_acorde_menor(self):
        # La menor: la, do, mi.
        slots = {0: {57: 1.0, 60: 1.0, 64: 1.0}}

        self.assertEqual(chord_name(slots, 0), "Lam")

    def test_el_bajo_desempata_entre_relativos(self):
        # Las mismas notas son Do mayor o La menor; manda la que está abajo.
        con_la_abajo = chord_name({0: {57: 1.5, 60: 1.0, 64: 1.0, 67: 1.0}}, 0)

        self.assertTrue(
            con_la_abajo.endswith("m"),
            "con el la abajo sale menor, salió %s" % con_la_abajo,
        )

    def test_un_compas_en_silencio_no_tiene_acorde(self):
        self.assertEqual(chord_name({}, 0), "")


if __name__ == "__main__":
    unittest.main()
