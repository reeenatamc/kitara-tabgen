//! Comprueba que una tablatura cuadra y saca su AlphaTex.
//!
//! La suma se hace con la aritmética exacta de `kitara-core`, no en coma flotante. Doce
//! corcheas de tresillo valen exactamente un 4/4, y cada una es 1/12, que en binario no se
//! puede escribir: sumándolas en `f64` el compás parece incompleto para siempre y este
//! comprobador rechazaría una tablatura correcta.
//!
//! Y la comparación es contra la indicación de compás de verdad, no contra la redonda: un
//! 3/4 suma 3/4, y antes se marcaba como descuadrado.

use kitara_core::alphatex::to_alphatex;
use kitara_core::model::{Fraction, Score};

fn main() {
    let path = std::env::args()
        .nth(1)
        .expect("uso: check <ruta de la tablatura .json>");
    let json = std::fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("no se pudo leer «{path}»: {error}"));
    let score: Score = serde_json::from_str(&json)
        .unwrap_or_else(|error| panic!("«{path}» no es una tablatura válida: {error}"));

    let mut descuadrados = 0;
    for (i, bar) in score.tracks[0].staves[0].bars.iter().enumerate() {
        let escrito = bar.voices[0]
            .beats
            .iter()
            .fold(Fraction::zero(), |acc, beat| {
                acc + beat.duration_in_whole_notes()
            });

        let signature = score
            .master_bars
            .get(i)
            .map(|master| master.time_signature)
            .unwrap_or_default();
        let cabe = Fraction::new(
            u64::from(signature.numerator),
            u64::from(signature.denominator),
        );

        if escrito != cabe {
            println!(
                "COMPAS {} suma {}/{} y cabe {}/{}",
                i + 1,
                escrito.numerator,
                escrito.denominator,
                cabe.numerator,
                cabe.denominator
            );
            descuadrados += 1;
        }
    }

    eprintln!(
        "compases {}, descuadrados {descuadrados}",
        score.bar_count()
    );
    println!("{}", to_alphatex(&score));
}
