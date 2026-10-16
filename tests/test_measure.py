"""Pruebas del medidor.

El medidor decide si un cambio del transcriptor mejora o empeora, así que un fallo aquí
manda el trabajo entero en la dirección contraria. Ya pasó: no sumaba la cejilla, y las dos
canciones que la llevan marcaban 1 % y 3 % con transcripciones que estaban bien. Con la
cejilla sumada, una de ellas pasó al 61 %.
"""

import unittest

from measure import common_run, found, melody_of, sequence_score_of


def nota(cuerda, traste):
    return {"string": cuerda, "fret": traste}


def pulso(notas, duracion=4):
    return {"duration": duracion, "notes": notas}


def partitura(compases, capo=0):
    """Una partitura mínima con lo que mira el medidor."""
    return {
        "tracks": [
            {
                "capo": capo,
                "staves": [{"bars": [{"voices": [{"beats": pulsos}]} for pulsos in compases]}],
            }
        ]
    }


class Melodia(unittest.TestCase):
    def test_la_melodia_es_la_nota_mas_aguda_del_pulso(self):
        # Primera al aire (Mi4, 64) con la sexta al aire debajo: manda la aguda.
        sc = partitura([[pulso([nota(1, 0), nota(6, 0)])]])

        melodia, total = melody_of(sc)[0]

        self.assertEqual(melodia, {(0, 64)})
        self.assertEqual(total, 2, "las dos notas se cuentan aunque sólo una sea melodía")

    def test_un_pulso_grave_no_cuenta_como_melodia(self):
        # La2 (45) está por debajo del suelo de melodía.
        sc = partitura([[pulso([nota(5, 0)])]])

        melodia, total = melody_of(sc)[0]

        self.assertEqual(melodia, set())
        self.assertEqual(total, 1)

    def test_la_cejilla_sube_la_altura(self):
        # El fallo que mandaba el trabajo en dirección contraria: con cejilla en el 2, la
        # primera al aire suena Fa#4 (66), no Mi4 (64).
        sin = melody_of(partitura([[pulso([nota(1, 0)])]], capo=0))[0][0]
        con = melody_of(partitura([[pulso([nota(1, 0)])]], capo=2))[0][0]

        self.assertEqual(sin, {(0, 64)})
        self.assertEqual(con, {(0, 66)})

    def test_las_notas_ligadas_no_son_ataques(self):
        atada = {"string": 1, "fret": 0, "tie_destination": True}
        sc = partitura([[pulso([atada])]])

        melodia, total = melody_of(sc)[0]

        self.assertEqual(total, 0, "una nota ligada ya sonaba, no es una nota nueva")
        self.assertEqual(melodia, set())

    def test_las_posiciones_avanzan_con_la_figura(self):
        # Cuatro negras: una por tiempo, en las semicorcheas 0, 4, 8 y 12.
        sc = partitura([[pulso([nota(1, i)]) for i in range(4)]])

        melodia, _ = melody_of(sc)[0]

        self.assertEqual(sorted(s for s, _ in melodia), [0, 4, 8, 12])

    def test_el_puntillo_alarga_la_figura(self):
        sc = partitura([[{"duration": 4, "dots": 1, "notes": [nota(1, 0)]}, pulso([nota(1, 2)])]])

        melodia, _ = melody_of(sc)[0]

        self.assertEqual(sorted(s for s, _ in melodia), [0, 6], "la negra con puntillo vale 6")


class Acertar(unittest.TestCase):
    def test_una_nota_en_su_sitio_cuenta(self):
        self.assertEqual(found({(4, 64)}, {(4, 64)}), {(4, 64)})

    def test_una_semicorchea_de_diferencia_se_perdona(self):
        # La tolerancia es el paso al que cuantiza el borrador.
        self.assertEqual(found({(4, 64)}, {(5, 64)}), {(4, 64)})

    def test_dos_semicorcheas_ya_no(self):
        self.assertEqual(found({(4, 64)}, {(6, 64)}), set())

    def test_la_altura_tiene_que_ser_la_misma(self):
        self.assertEqual(found({(4, 64)}, {(4, 65)}), set())


class Secuencia(unittest.TestCase):
    def test_la_misma_melodia_da_todo(self):
        self.assertEqual(common_run([60, 62, 64], [60, 62, 64]), 3)

    def test_las_notas_de_mas_por_medio_no_estorban(self):
        # Lo que la hace invariante al tempo: sobra material entre las notas buenas.
        self.assertEqual(common_run([60, 62, 64], [60, 99, 62, 98, 64]), 3)

    def test_el_orden_importa(self):
        self.assertEqual(common_run([60, 62, 64], [64, 62, 60]), 1)

    def test_una_melodia_que_no_esta_da_cero(self):
        self.assertEqual(common_run([60, 62], [70, 71]), 0)

    def test_el_porcentaje_no_mira_el_ritmo(self):
        # Las mismas alturas con las figuras cambiadas: la medida por compás las daría por
        # falladas y ésta las reconoce.
        mano = partitura([[pulso([nota(1, 0)]), pulso([nota(1, 2)])]])
        otro_ritmo = partitura([[pulso([nota(1, 0)], 8), pulso([nota(1, 2)], 2)]])

        self.assertEqual(sequence_score_of(mano, otro_ritmo), 100.0)


if __name__ == "__main__":
    unittest.main()
