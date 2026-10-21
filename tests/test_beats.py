"""Pruebas de las partes del seguidor de pulso que no necesitan el modelo.

El recorte en ventanas, el pegado y la busqueda de picos son los pasos donde desviarse del
original mueve los pulsos sin que nada avise, porque el resultado sigue siendo una lista de
numeros plausible. Son aritmetica pura y se prueban sin cargar 190 MB de red neuronal.
"""

import unittest

import numpy as np

from transcriber import beats


class VentanasDeEspectrograma(unittest.TestCase):
    def test_una_grabacion_corta_cabe_en_una_ventana(self):
        spect = np.ones((300, beats.MEL_BINS), dtype=np.float32)
        chunks, starts = beats._windows(spect)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].shape, (beats.CHUNK, beats.MEL_BINS))

    def test_toda_ventana_sale_del_tamano_que_pide_el_modelo(self):
        spect = np.ones((4000, beats.MEL_BINS), dtype=np.float32)
        chunks, _ = beats._windows(spect)
        for chunk in chunks:
            self.assertEqual(chunk.shape, (beats.CHUNK, beats.MEL_BINS))

    def test_la_primera_ventana_empieza_antes_del_principio(self):
        """El borde se rellena con ceros porque el modelo no predice bien en los extremos."""
        spect = np.ones((4000, beats.MEL_BINS), dtype=np.float32)
        _, starts = beats._windows(spect)
        self.assertEqual(starts[0], -beats.BORDER)

    def test_la_ultima_ventana_acaba_donde_acaba_la_grabacion(self):
        spect = np.ones((4000, beats.MEL_BINS), dtype=np.float32)
        _, starts = beats._windows(spect)
        self.assertEqual(starts[-1] + beats.CHUNK - beats.BORDER, len(spect))

    def test_las_ventanas_cubren_todos_los_cuadros(self):
        spect = np.ones((4000, beats.MEL_BINS), dtype=np.float32)
        _, starts = beats._windows(spect)
        cubierto = np.zeros(len(spect), dtype=bool)
        for start in starts:
            cubierto[start + beats.BORDER : start + beats.CHUNK - beats.BORDER] = True
        self.assertTrue(cubierto.all())


class PegadoDePredicciones(unittest.TestCase):
    def test_lo_que_escribe_una_ventana_temprana_sobrevive_a_la_siguiente(self):
        """Es el `keep_first` del original: donde dos ventanas se pisan, manda la primera."""
        total = beats.CHUNK * 2
        step = beats.CHUNK - 2 * beats.BORDER
        starts = [-beats.BORDER, -beats.BORDER + step]
        pieces = [
            (np.full(beats.CHUNK, 1.0, dtype=np.float32), np.zeros(beats.CHUNK, np.float32)),
            (np.full(beats.CHUNK, 2.0, dtype=np.float32), np.zeros(beats.CHUNK, np.float32)),
        ]
        beat, _ = beats._join(pieces, starts, total)
        self.assertEqual(beat[0], 1.0)

    def test_los_cuadros_que_nadie_cubre_quedan_en_probabilidad_cero(self):
        beat, down = beats._join([], [], 10)
        self.assertTrue((beat == -1000.0).all())
        self.assertTrue((down == -1000.0).all())


class BusquedaDePicos(unittest.TestCase):
    def test_un_maximo_claro_es_un_pico(self):
        logits = np.full(40, -5.0, dtype=np.float32)
        logits[20] = 3.0
        self.assertEqual(list(beats._peaks(logits)), [20])

    def test_un_maximo_con_probabilidad_por_debajo_de_media_no_cuenta(self):
        """El umbral es logit cero, o sea media probabilidad: por debajo no es un pulso."""
        logits = np.full(40, -5.0, dtype=np.float32)
        logits[20] = -0.5
        self.assertEqual(len(beats._peaks(logits)), 0)

    def test_de_dos_cuadros_vecinos_solo_gana_el_mas_alto(self):
        logits = np.full(40, -5.0, dtype=np.float32)
        logits[20] = 1.0
        logits[21] = 3.0
        self.assertEqual(list(beats._peaks(logits)), [21])

    def test_dos_picos_separados_sobreviven_los_dos(self):
        logits = np.full(60, -5.0, dtype=np.float32)
        logits[10] = 3.0
        logits[40] = 3.0
        self.assertEqual(list(beats._peaks(logits)), [10, 40])


class JuntarPicosPegados(unittest.TestCase):
    def test_dos_cuadros_seguidos_se_juntan_en_su_promedio(self):
        self.assertEqual(list(beats._merge(np.array([10, 11]))), [10.5])

    def test_dos_picos_separados_no_se_juntan(self):
        self.assertEqual(list(beats._merge(np.array([10, 20]))), [10.0, 20.0])

    def test_sin_picos_no_hay_nada_que_juntar(self):
        self.assertEqual(len(beats._merge(np.array([]))), 0)

    def test_un_solo_pico_se_queda_donde_esta(self):
        self.assertEqual(list(beats._merge(np.array([7]))), [7.0])


class RecetaDelModelo(unittest.TestCase):
    def test_los_cuadros_por_segundo_salen_del_salto_de_la_ventana(self):
        """50 cuadros por segundo es 22050 entre 441; si no cuadra, los tiempos salen mal."""
        self.assertAlmostEqual(beats.SAMPLE_RATE / beats.HOP, beats.FPS)
