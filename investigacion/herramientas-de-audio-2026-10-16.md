# Investigación de audio para el transcriptor de guitarra a tab

Fecha: 2026-10-16. Solo lectura y búsqueda; nada instalado ni descargado.

Convención de confianza:
- [REPO] lo comprobé abriendo la página del repositorio (existe, licencia, pesos o instalación).
- [PAPER] lo dice un paper, blog o resumen; no lo verifiqué en el repo ni lo medí.
- [MEMORIA] lo sé de antes y no pude reconfirmarlo en esta sesión; trátalo como pista.
- NC = licencia no comercial.

Límite honesto: WebFetch resume las páginas con un modelo pequeño, así que cifras finas (F1, tiempos) deben leerse en la fuente antes de decidir. No encontré ningún dato de tiempo por minuto de audio en CPU Intel para la mayoría de herramientas; donde lo doy, lo marco como estimación.

## 0. Diagnóstico previo: dos de los problemas probablemente no son de modelo

1. Pulso al doble (117 por 60). `librosa.beat.beat_track` tiene un prior de tempo centrado en `start_bpm=120`; en música lenta tiende a elegir el doble. Es un sesgo conocido [MEMORIA]. Antes de cambiar de modelo conviene probar `start_bpm=60` o `tempo` fijo, o `librosa.feature.tempo` con `prior` propio. Un estudio de 2026 sobre fallos de seguimiento de pulso atribuye el doble tempo en música lenta al mínimo de 55 BPM del DBN de madmom y recomienda estimación multi-hipótesis de tempo [PAPER: arxiv.org/abs/2605.12287; el resumen no nombra qué sistemas fallan]. Moraleja: cualquier tracker necesita una regla de desambiguación de octava; ninguno la resuelve sola.
2. Pérdida de melodía del 62 % al 35 % por tus reglas. Un trabajo de licenciatura de Lund (2026) adaptó basic-pitch para tab y encontró lo contrario a tu enfoque: bajar la duración mínima de nota a 40 ms captura pasajes rápidos pero genera "efecto escopeta" de falsos positivos; luego un filtro específico de guitarra (notas físicamente imposibles) subió precisión y F1 y bajó el fallo del Viterbi de fingering de 11,13 % a menos de 1 % [PAPER, tesis de estudiantes, tomar con cautela: lup.lub.lu.se/student-papers/record/9226851/file/9226852.pdf]. La idea útil: filtrar por reglas físicas de la guitarra (rango E2 a E6, máximo 6 notas simultáneas, alcance de la mano, una nota por cuerda) en vez de por umbral de amplitud.

## 1. Separación de fuentes

### Demucs htdemucs_6s
- https://github.com/facebookresearch/demucs. Licencia MIT [REPO]. Repo archivado el 2025-01-01, sin mantenimiento; fork de correcciones en github.com/adefossez/demucs [REPO].
- El README califica el stem de guitarra como "okay quality" y el modelo de 6 fuentes como experimental; el de piano tiene mucho sangrado [REPO].
- CPU: el README estima unas 1,5 veces la duración de la pista [REPO]. Eso son unos 90 s por minuto de audio, orden de magnitud; en tu Intel sin AVX512 puede ser peor. Funciona con PyTorch 2.2.2 (modelo antiguo y estable) [MEMORIA].
- Ataca: voz y banda. Mejora esperada: grande en canciones con banda, nula o negativa en guitarra sola (artefactos). Úsalo solo cuando la pista tenga voz o batería.

### python-audio-separator
- https://github.com/nomadkaraoke/python-audio-separator. MIT [REPO]. Instala con `pip install "audio-separator[cpu]"`, Python 3.10 o superior, y ejecuta modelos Roformer (BS y MelBand), Demucs v4 incluido htdemucs_6s, MDX-Net (onnx) y VR [REPO].
- Su README no lista ningún modelo solo de guitarra; el stem de guitarra viene de htdemucs_6s [REPO]. La lista completa de modelos (`--list_models`) no la pude abrir; ahí podría haber más.
- Sirve como envoltorio único para probar varios modelos con la misma interfaz. Trae `--chunk_duration` para no agotar RAM [REPO].

### BS-RoFormer y Mel-RoFormer
- Son arquitecturas SOTA en separación de voz/batería/bajo/otros [PAPER: arxiv.org/html/2310.01809v1]. Los pesos comunitarios más usados son de voz (por ejemplo el de Kimberley Jensen, MIT según un port) [PAPER/blog]. Hay un port de BS-RoFormer con licencia CC-BY-NC-4.0 (NC) y otro pequeño MIT; la licencia depende de cada checkpoint. Un paquete de inferencia de seis stems (BS-RoFormer-SW) reporta que su checkpoint por defecto vino de una cuenta de Hugging Face borrada (descubierto en 2026-06) [PAPER/blog: github.com/openmirlab/bs-roformer-infer]. Riesgo de que los pesos desaparezcan.
- MVSep ofrece un modelo de guitarra (acústica y eléctrica) basado en MDX23C/Mel-RoFormer: SDR de guitarra 7,02 para la variante MelRoformer frente a 5,22 de Demucs4HT [PAPER/blog: mvsep.com/algorithms/17]. Es servicio web, no pesos descargables que yo haya verificado. No encontré un checkpoint abierto de guitarra con Mel-RoFormer.
- CPU: los Roformer grandes son pesados; sin GPU esperar varias veces el tiempo real [MEMORIA, sin dato]. No recomendado para tu Mac salvo pruebas puntuales.

### Evidencia de que separar mejora la transcripción
- No encontré ninguna ablación publicada que mida basic-pitch (o un transcriptor de guitarra) sobre mezcla frente a stem de Demucs. Un survey de 2024, "Source Separation & Automatic Transcription for Music" (arxiv.org/pdf/2412.06703), cubre el cruce pero no lo pude leer completo [PAPER].
- Para acordes sí hay un dato: un trabajo de APSIPA 2025 reporta que separar fuentes antes de BTC mejoró la precisión de acordes (BTC en triadas: 75,52 %) [PAPER: webdev.apsipa.org/proceedings/2025/papers/APSIPA2025_P307.pdf].
- Conclusión: es una hipótesis razonable, hay que medirla en tu propio corpus (ver experimento 1).

## 2. Pulso, compás y estructura

### beat_this (CPJKU)
- https://github.com/CPJKU/beat_this. MIT para código y pesos; aviso de que algunos archivos de entrenamiento tienen copyright o CC limitada [REPO]. ISMIR 2024 (Foscarin, Schlüter, Widmer).
- Pesos descargables: `final0` (78 MB) y modelos `small0-2` (8 MB cada uno) [REPO]. CPU con `--gpu=-1`. Requiere PyTorch 2.0 o superior (cabe en 2.2.2) más tqdm, einops, soxr, rotary-embedding-torch [REPO]. No publica tiempos en CPU.
- Sin DBN: elige picos, así que no impone tempo ni compás, lo cual evita los límites tipo 55 BPM pero también significa que el doble tempo puede aparecer y hay que resolverlo con una regla tuya (ver 0). Entrenado también con solos de instrumento, útil para guitarra [PAPER]. Peor en métricas de continuidad y en géneros poco representados [PAPER: arxiv.org/abs/2407.21658].
- Ataca: pulso al doble y compases partidos. Ayuda esperada: alta en la calidad de la rejilla de golpes y downbeats; el doble tempo se arregla comparando con el tempo mediano de intervalos y una regla de octava.

### All-In-One (mir-aidj)
- https://github.com/mir-aidj/all-in-one. MIT para el código; no se aclara licencia de pesos [REPO]. Pesos `harmonix-all` (ensamble de 8) y folds, entrenados en Harmonix Set [REPO]. Da beats, downbeats, tempo y segmentos funcionales (verso, coro...).
- CPU funciona. El único tiempo publicado es de GPU (33 min de audio en 73 s con RTX 4090) [REPO]. Dependencias: NATTEN (en macOS se instala solo según el README, pero con PyTorch 2.2.2 el emparejamiento de versiones puede dar guerra [MEMORIA]) y madmom desde GitHub [REPO].
- Ataca: estructura (para el punto 6) y downbeats. Pesado de instalar en tu Mac; segunda prioridad.

### madmom
- https://github.com/CPJKU/madmom. Código BSD, pero modelos y datos bajo CC BY-NC-SA 4.0: NC [REPO]. No es seguro con tu criterio de licencia si el proyecto pudiera volverse comercial. Problemas conocidos con Python 3.10 o superior y NumPy nuevos (beat_this lo señala diciendo que la versión de PyPI tiene límites) [REPO]. Descártalo salvo como referencia de comparación.

### BeatNet
- CRNN con filtro de partículas, tiempo real [MEMORIA]; no abrí su repo ni licencia. Sin evidencia nueva que lo ponga por encima de beat_this.

## 3. Acordes y tonalidad

El hallazgo principal: tus acordes salen de una adivinanza sobre notas detectadas, lo cual es circular (el bajo fantasma del 70 % sale de ahí). Los modelos de acordes parten del audio (cromagrama), no de las notas.

### BTC (Bi-directional Transformer for Chord recognition, ISMIR 2019)
- Repo original https://github.com/jayg996/BTC-ISMIR19 (último push 2020 según un agregador [PAPER]); empaquetado no oficial en Hugging Face `puar-playground/btc-chord`: `predict` simple, CPU, vocabulario grande de 170 tipos de acorde o solo mayor/menor, pesos sin cambios del lanzamiento original, que es MIT [PAPER/blog: huggingface.co/puar-playground/btc-chord]. Verifica el LICENSE del repo original antes de usarlo.
- Precisión de triadas reportada 75,52 % en el trabajo de APSIPA 2025, que además mejora con separación previa [PAPER]. Un preprint de 2026 afirma que un modelo basado en eventos lo supera, más al exigir acordes complejos [PAPER: arxiv.org/pdf/2604.24386].
- CPU: modelo pequeño, deberías poder correrlo en segundos por minuto de audio [MEMORIA, sin dato].
- Ataca: acordes mal adivinados y, por cascada, el bajo fantasma. Ayuda esperada: alta en acordes mayores/menores; para fingerstyle con notas sueltas, los acordes serán menos fiables.

### Chordino / NNLS-Chroma (QMUL)
- Plugin Vamp; en un meta-estudio antiguo Chordino marcaba cerca del 76 % [PAPER: arxiv.org/pdf/1109.0420]. Licencia GPL [MEMORIA]. Se usa desde Python con `chord-extractor`; no abrí su repo.
- Pro: ligero, sin PyTorch. Contra: dependencia nativa Vamp en macOS Intel; precisión inferior a modelos neuronales.

### autochord
- https://pypi.org/project/autochord. Usa NNLS-Chroma más Bi-LSTM-CRF con TensorFlow, solo 25 clases (mayor, menor, sin acorde) [PAPER/pypi]. Choca con TensorFlow y con tu stack; no recomendado.

### essentia
- https://github.com/MTG/essentia. AGPLv3 [REPO]; su README solo menciona wheels para Linux x86_64, no macOS [REPO], aunque en PyPI puede haber wheels de macOS [MEMORIA, sin verificar]. AGPL es restrictiva si algún día distribuyes la herramienta. Tiene detección de tonalidad y acordes clásicos, y modelos TempoCNN; los modelos preentrenados tienen licencias propias, algunas NC [MEMORIA]. Útil sobre todo para `Key` (tonalidad por perfiles). Bajo en prioridad por la licencia y la instalación.

### Acordes: no encontré
Nada reciente (ChordFormer, ChordMini u otros 2024 a 2026) con pesos abiertos y CPU verificados.

## 4. Altura y ataques

### basic-pitch (lo que ya usas): ajustes pendientes
- https://github.com/spotify/basic-pitch. Apache-2.0, backends TF, CoreML, TFLite y ONNX; Python 3.11 soportado [REPO]. El README no documenta `onset_threshold`, `frame_threshold`, `minimum_note_length`, `melodia_trick` ni `multiple_pitch_bends`; existen en `predict()` según mi memoria [MEMORIA], léelos en el código. El experimento más barato de todo el informe es barrer esos parámetros con el modelo sin tu limpieza posterior.

### SwiftF0
- https://github.com/lars76/swift-f0. MIT [REPO]. Detector monofónico, solo onnxruntime y numpy como dependencias duras [REPO]. Rango 46,9 a 2093,75 Hz (G1 a C7), cuadros de 16 ms, devuelve pitch, confianza y loudness, y trae `segment_notes` y `export_to_midi` [REPO]. Unas 180 veces tiempo real en un núcleo de CPU de portátil según el autor [REPO]; 91,8 % de media armónica a 10 dB de SNR, 42 veces más rápido que CREPE [PAPER: arxiv.org/abs/2508.18440].
- Solo monofónico: sirve para pistas de melodía aislada (por ejemplo el stem de voz o una línea de guitarra), no para la guitarra fingerstyle entera. Posible uso: segunda opinión sobre la línea de melodía para recuperar notas que tus reglas descartaron. Ayuda esperada: media para melodía; no resuelve bajo ni acordes.

### PESTO
- https://github.com/SonyCSLParis/pesto. LGPL-3.0 [REPO] (permite usarla como dependencia, con condiciones). Monofónico; en un i7-1185G7 procesó 2 min 51 s de audio en unos 13 s (12 veces tiempo real), CREPE tardó unos 12 min [REPO]. Misma limitación monofónica que SwiftF0.

### CREPE
- https://github.com/marl/crepe. MIT según la insignia [REPO]. Requiere TensorFlow 2.x; lento en CPU (ver cifra de PESTO). Superado en velocidad por SwiftF0 y PESTO; no lo uses.

### RMVPE
- Detector de F0 robusto con música de fondo, pensado para voz cantada [MEMORIA]; no abrí repo ni licencia. Sin evidencia de que ayude con guitarra.

### Armónicos como notas (octava y docena)
- No encontré una herramienta lista. Estrategia habitual: tras basic-pitch, una nota candidata es sospechosa si existe otra nota 12 o 19 semitonos más grave, empieza casi a la vez y tiene mayor amplitud (supresión por relación armónica). Esto se puede implementar con las probabilidades de salida de basic-pitch (`model_output["contour"]`/`note`) y se mide fácil con mir_eval [mi sugerencia, no probada]. La poda por reglas físicas de guitarra (sección 0) también elimina muchos casos.

## 5. Preprocesamiento

- DeepFilterNet: https://github.com/Rikorose/DeepFilterNet, MIT o Apache-2.0 a elegir [REPO]. Es de voz (48 kHz), no de música; un paper de 2025 dice que su desreverberación es débil [PAPER: ncbi.nlm.nih.gov/pmc/articles/PMC11820353]. No encontré ninguna evaluación en transcripción de música. No lo recomiendo: puede comerse armónicos y ataques de la guitarra.
- Normalización: sencilla y sin riesgo en teoría (normalizar el pico o a LUFS fijo antes de basic-pitch, ya que sus umbrales dependen del nivel) [mi sugerencia]. Barato de probar.
- pedalboard: https://github.com/spotify/pedalboard, GPLv3 [REPO]. Hay wheels para macOS Intel [REPO]. Reverb, compresor, limitador y ganancia [REPO]; no trae denoise [REPO]. Útil para aumentar datos o ecualizar (por ejemplo un filtro paso alto en 70 Hz), pero la licencia GPLv3 obliga si distribuyes.
- resemble-enhance: no lo abrí; también es de voz [MEMORIA]. Omitido.
- No encontré evidencia de que desreverberar mejore la transcripción musical. Un paper de 2013 lo sugiere para seguimiento de pulso [PAPER: homepages.tuni.fi/tuomas.virtanen/papers/Mahkonen_DAFX2013.pdf].

## 6. Aprovechar la repetición

- No encontré ningún trabajo o herramienta que use la autosimilitud para limpiar notas de una transcripción de guitarra. Lo más cercano: REPET (modelo de segmento repetido promediado para separar voz de acompañamiento) [PAPER/Northwestern]; y un trabajo de 2020 que usa estadísticas no locales (repeticiones a nivel de compás y frase) para guiar la transcripción de piano audio a partitura [PAPER: arxiv.org/pdf/2008.12710].
- MSAF: https://github.com/urinieto/msaf, MIT, 1.375 commits, 560 estrellas [REPO]. No pude confirmar compatibilidad con Python 3.11 ni fecha de la última actividad. Para estructura probablemente basta la salida de All-In-One o una matriz de autosimilitud propia con librosa (`librosa.segment.recurrence_matrix` sobre un cromagrama sincronizado a compás) [mi sugerencia].
- Idea concreta (propia, no validada en literatura): una vez que cuantizas a compases, compara compases por similitud de cromagrama; entre compases casi idénticos, vota nota por nota: conserva una nota si aparece en la mayoría de repeticiones (recupera notas perdidas por el umbral), descarta las que aparecen una sola vez con baja amplitud. Funciona mejor en música con repetición exacta (fingerstyle con patrones de arpegio).

## 7. Librerías base

- mir_eval: para medir notas (F1 de onset, con o sin offset) y beats. Licencia MIT [MEMORIA]; no abrí el repo. Imprescindible para que cada experimento tenga número.
- nnAudio: espectrogramas en PyTorch con filtros de CQT; MIT [MEMORIA]. Solo sirve si montas un modelo propio; no es prioridad.
- torchaudio: ya dependiente de PyTorch 2.2.2; resample y carga. Sin más.
- music21 y partitura: salida simbólica; no cambian la precisión del audio.
- Sobre el entrenamiento propio: el trabajo procedural de Klangio (arxiv.org/abs/2508.07987, CC BY-NC-SA el paper) preentrenó un Onsets and Frames con tabs sintetizadas por Karplus-Strong y subió el F1 en GuitarSet de 81,42 a 83,49 al afinar con real, y de 63,32 a 77,45 con solo 60 grabaciones reales [PAPER]. No estudié transcriptores completos (descartado en tu encargo), pero la idea de afinar basic-pitch u otro modelo pequeño con pocos datos propios queda anotada.

## 8. Novedades 2024 a 2026

- ISMIR 2024: Beat This (arriba); GAPS (ya cubierto).
- ISMIR 2025: GOAT, gran dataset de audio de guitarra emparejado con tablaturas con renderizados de amplificador (https://ismir2025program.ismir.net/poster_245.html) [PAPER, no lo abrí]; transcripción conjunta de rasgueos y acordes de guitarra acústica (Murgul y colaboradores) [PAPER]; datos procedurales para fingerpicking (arriba). Un modelo de transcripción en tiempo real de Yamaha aparece para ISMIR 2026 [PAPER: yamaha.com/en/tech-design/research/news/26_ismir].
- 2025 a 2026: el análisis de fallos del seguimiento de pulso (SMC) y el trabajo de acordes de eventos (arriba).
- Demucs archivado (enero 2025): cualquier solución basada en Demucs debe pensar en el fork o en congelar la versión.
- Industria (Moises, Spotify, Meta): no encontré nada relevante verificable en esta búsqueda; no afirmo nada.

## 9. Resumen de licencias

- Permisivas: beat_this MIT, All-In-One MIT (pesos sin aclarar), Demucs MIT, audio-separator MIT, SwiftF0 MIT, basic-pitch Apache-2.0, DeepFilterNet MIT/Apache, MSAF MIT, BTC MIT (según el empaquetado de HF; verificar).
- Con condiciones: PESTO LGPL-3.0, pedalboard GPLv3, essentia AGPLv3, Chordino GPL (memoria).
- NC: modelos de madmom (CC BY-NC-SA 4.0), un port de BS-RoFormer en CC-BY-NC-4.0, el paper del trabajo de Klangio (CC BY-NC-SA).

## 10. Top 5 por impacto esperado y facilidad de prueba

Cada experimento usa un conjunto fijo de 5 a 10 clips con anotación manual de pulso o notas (o los que ya mediste) y mir_eval como juez.

1. Arreglar el tempo con prior y regla de octava, y compararlo con beat_this.
   - Problema: pulso al doble y compases partidos. Ayuda esperada: alta, casi seguro.
   - Experimento: en tus clips con tempo conocido (60 bpm), correr `librosa.beat.beat_track(start_bpm=60)` y, aparte, `beat_this` (`pip install beat-this` en un venv aparte, small0 primero) con la mediana de intervalos entre beats; aplicar regla "si tempo > 100 y la mitad es plausible por energía de los tiempos alternos, usar la mitad". Medir F1 de beats con mir_eval y tasa de error de octava.

2. Barrer los parámetros de basic-pitch y reemplazar el umbral de amplitud por filtros de física de guitarra.
   - Problema: la melodía cae del 62 % al 35 %. Ayuda esperada: alta, recupera casi todo lo perdido por tus reglas.
   - Experimento: congelar salida cruda de basic-pitch con `minimum_note_length` 40 a 127 ms, `onset_threshold` 0,3 a 0,6 y `melodia_trick` activo; medir F1 de notas contra tu referencia. Después, activar de a una cada regla de limpieza (rango E2 a E6, máximo 6 notas, una por cuerda, poda de armónicos) y ver cuál baja el F1; quitar la que más daño haga. Seguir el enfoque de la tesis de Lund.

3. Acordes desde el audio con BTC, y sustituir el bajo derivado de acordes por una comprobación cruzada.
   - Problema: acordes mal adivinados y bajo fantasma 70 %. Ayuda esperada: media a alta.
   - Experimento: correr BTC (paquete HF `puar-playground/btc-chord`, vocabulario mayor/menor) sobre 5 clips; comparar con tus acordes adivinados contra una referencia manual de acordes por compás. Luego generar el bajo solo cuando la fundamental del acorde de BTC aparece entre las notas graves detectadas (grave = por debajo de MIDI 55) y medir qué fracción de bajos escritos queda fantasma.

4. Separar con htdemucs_6s solo las canciones con voz y banda, y comparar el F1 de notas.
   - Problema: empeora todo con voz y banda. Ayuda esperada: alta en esos casos, ninguna o negativa en guitarra sola.
   - Experimento: instalar `audio-separator[cpu]` en un venv aparte, correr htdemucs_6s sobre 3 canciones con banda (anotar el tiempo por minuto), pasar basic-pitch al stem de guitarra y a la mezcla, y comparar F1 de notas contra la referencia. Decidir con un detector simple (porcentaje de energía fuera de la banda de guitarra) cuándo separar.

5. Votación entre compases repetidos para recuperar y limpiar notas.
   - Problema: pérdida de notas reales y falsos positivos sueltos. Ayuda esperada: media, solo en música repetitiva; es lo más especulativo (sin precedente publicado que encontré).
   - Experimento: con la rejilla de compases del punto 1, calcular la distancia entre cromagramas por compás (librosa `chroma_cqt`), agrupar compases con distancia baja y, dentro de cada grupo, conservar notas presentes en al menos la mitad de las repeticiones con la probabilidad de basic-pitch sumada. Medir el F1 de notas en una canción con estrofas repetidas, antes y después.

Orden de trabajo sugerido: 1 y 2 en el mismo día (no requieren instalar casi nada); luego 3; 4 solo si el corpus tiene bandas; 5 al final porque depende de que 1 y 2 estén bien.

## 11. Qué no encontré

- Ninguna ablación publicada de separación de fuentes sobre transcripción de guitarra con basic-pitch.
- Ningún modelo abierto específico de guitarra acústica para separación (solo el stem de htdemucs_6s y MVSep como servicio).
- Tiempos medidos en CPU Intel para beat_this, All-In-One, BTC y Roformer.
- Acordes: nada nuevo con pesos abiertos de 2024 a 2026 verificado.
- Industria: nada verificable.
