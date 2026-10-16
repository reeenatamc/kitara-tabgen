"""Dónde está el repo de kitara.

Los archivos de canción leen y escriben dentro de kitara, y la ruta estaba clavada en cada
uno. El repo se renombró una vez de `fretwork` a `kitara` y tres archivos se quedaron
apuntando al nombre viejo sin que nada avisara: simplemente dejaron de correr.

Se puede cambiar con la variable `KITARA_REPO` si está en otro sitio.
"""

import os
from pathlib import Path

#: Dónde se busca kitara si no se dice otra cosa.
DEFAULT = Path.home() / "Documents" / "GitHub" / "kitara"

KITARA = Path(os.environ.get("KITARA_REPO", DEFAULT))


def song(slug):
    """La ruta del JSON de una canción dentro de kitara."""
    return KITARA / "songs" / f"{slug}.json"


def guide(slug):
    """La ruta del JSON de su guía."""
    return KITARA / "guides" / f"{slug}.json"


#: Los arreglos superados viven aquí, no en kitara: eran pasos de una iteración.
ARCHIVE = Path(__file__).resolve().parent / "archive"


def archived_song(slug):
    """La ruta de una canción archivada, dentro de este repo.

    Algunos arreglos se hicieron encima del anterior, y el anterior quedó superado y fuera
    de kitara. Los scripts que los leen apuntan aquí para seguir corriendo.
    """
    return ARCHIVE / "songs" / f"{slug}.json"


def archived_guide(slug):
    """La ruta de la guía de una canción archivada."""
    return ARCHIVE / "guides" / f"{slug}.json"


def require():
    """Falla con un mensaje claro si kitara no está donde se espera.

    Sin esto el error es un `FileNotFoundError` de un archivo suelto, y lo que pasa de verdad
    es que falta el repo entero o está en otro sitio.
    """
    if not KITARA.is_dir():
        raise SystemExit(
            f"No encuentro kitara en {KITARA}.\n"
            f"Si está en otro sitio: KITARA_REPO=/ruta/a/kitara {os.path.basename(__file__)}"
        )
    return KITARA
