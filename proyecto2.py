import re
from difflib import SequenceMatcher


ABREVIATURAS = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "nw": "northwest",
    "ne": "northeast",
    "sw": "southwest",
    "se": "southeast",
    "ave": "avenue",
    "st": "street",
    "blvd": "boulevard",
    "rd": "road",
    "dr": "drive",
    "ln": "lane",
    "hwy": "highway",
    "bldg": "building",
    "ste": "suite",
}

PALABRAS_RUIDO = {
    "addition",
    "construction",
    "project",
    "renovation",
}

PATRONES_IDENTIFICADORES = {
    "phase": re.compile(r"\b(?:phase|ph)\s+([a-z0-9]+)\b"),
    "tower": re.compile(r"\btower\s+([a-z0-9]+)\b"),
    "building": re.compile(r"\bbuilding\s+([a-z0-9]+)\b"),
}


def _normalizar(texto: str) -> str:
    """Lowercase text, strip punctuation, and expand known abbreviations."""
    texto = re.sub(r"[^a-z0-9\s]", " ", texto.lower())
    palabras = [ABREVIATURAS.get(palabra, palabra) for palabra in texto.split()]
    return " ".join(palabras)


def _extraer_identificadores(texto_normalizado: str) -> dict[str, set[str]]:
    """Extract phase, tower, and building identifiers for hard-fail checks."""
    return {
        tipo: set(patron.findall(texto_normalizado))
        for tipo, patron in PATRONES_IDENTIFICADORES.items()
    }


def _quitar_ruido(texto_normalizado: str) -> str:
    palabras = [
        palabra
        for palabra in texto_normalizado.split()
        if palabra not in PALABRAS_RUIDO
    ]
    return " ".join(palabras)


def _quitar_detalles_sin_contraparte(texto1: str, texto2: str) -> tuple[str, str]:
    tokens1 = set(texto1.split())
    tokens2 = set(texto2.split())
    numeros1 = {token for token in tokens1 if token.isdigit()}
    numeros2 = {token for token in tokens2 if token.isdigit()}
    cardinales = {
        "north", "south", "east", "west",
        "northeast", "northwest", "southeast", "southwest",
    }
    direcciones1 = tokens1 & cardinales
    direcciones2 = tokens2 & cardinales

    quitar1 = (numeros1 - numeros2) if numeros2 else numeros1
    quitar2 = (numeros2 - numeros1) if numeros1 else numeros2
    if not direcciones2:
        quitar1 |= direcciones1
    if not direcciones1:
        quitar2 |= direcciones2

    texto1_ajustado = " ".join(token for token in texto1.split() if token not in quitar1)
    texto2_ajustado = " ".join(token for token in texto2.split() if token not in quitar2)
    return texto1_ajustado, texto2_ajustado


def _hay_conflicto_critico(texto1: str, texto2: str) -> bool:
    identificadores1 = _extraer_identificadores(texto1)
    identificadores2 = _extraer_identificadores(texto2)
    conflicto_etiquetado = any(
        identificadores1[tipo]
        and identificadores2[tipo]
        and identificadores1[tipo] != identificadores2[tipo]
        for tipo in PATRONES_IDENTIFICADORES
    )
    numeros1 = set(re.findall(r"\b\d+\b", texto1))
    numeros2 = set(re.findall(r"\b\d+\b", texto2))
    conflicto_numerico = bool(
        numeros1
        and numeros2
        and not numeros1.issubset(numeros2)
        and not numeros2.issubset(numeros1)
    )

    cardinales_opuestos = {
        ("north", "south"),
        ("east", "west"),
        ("northeast", "southwest"),
        ("northwest", "southeast"),
    }
    tokens1 = set(texto1.split())
    tokens2 = set(texto2.split())
    conflicto_cardinal = any(
        (
            a in tokens1
            and b in tokens2
            and a not in tokens2
            and b not in tokens1
        )
        or (
            b in tokens1
            and a in tokens2
            and b not in tokens2
            and a not in tokens1
        )
        for a, b in cardinales_opuestos
    )

    return conflicto_etiquetado or conflicto_numerico or conflicto_cardinal


def _comparar_proyectos(
    nombre_sucio: str,
    nombre_oficial: str,
) -> tuple[float, dict[str, float]]:
    sucio_normalizado = _normalizar(nombre_sucio)
    oficial_normalizado = _normalizar(nombre_oficial)
    sucio_limpio = _quitar_ruido(sucio_normalizado)
    oficial_limpio = _quitar_ruido(oficial_normalizado)
    sucio_comparable, oficial_comparable = _quitar_detalles_sin_contraparte(
        sucio_limpio,
        oficial_limpio,
    )

    similitud_normalizada = SequenceMatcher(
        None,
        sucio_comparable,
        oficial_comparable,
    ).ratio()
    similitud_textual = SequenceMatcher(
        None,
        sucio_comparable,
        oficial_comparable,
    ).ratio()
    tokens_sucios = set(sucio_comparable.split())
    tokens_oficiales = set(oficial_comparable.split())
    union_tokens = tokens_sucios | tokens_oficiales
    similitud_palabras = (
        len(tokens_sucios & tokens_oficiales) / len(union_tokens)
        if union_tokens
        else 0.0
    )

    tokens_antes_del_filtro = sucio_normalizado.split() + oficial_normalizado.split()
    tokens_despues_del_filtro = sucio_limpio.split() + oficial_limpio.split()
    retencion_sin_ruido = (
        len(tokens_despues_del_filtro) / len(tokens_antes_del_filtro)
        if tokens_antes_del_filtro
        else 0.0
    )
    identificadores_compatibles = not _hay_conflicto_critico(
        sucio_normalizado,
        oficial_normalizado,
    )

    puntaje = round(
        (similitud_textual * 0.8 + similitud_palabras * 0.2) * 100,
        2,
    )
    if not identificadores_compatibles:
        puntaje = 0.0

    metricas = {
        "normalization": round(similitud_normalizada * 100, 2),
        "word_overlap": round(similitud_palabras * 100, 2),
        "text_similarity": round(similitud_textual * 100, 2),
        "identifier_compatibility": 100.0 if identificadores_compatibles else 0.0,
        "noise_retention": round(retencion_sin_ruido * 100, 2),
    }
    return puntaje, metricas


def match_project_with_metrics(
    dirty_name: str,
    known_projects: list[str],
    threshold: float = 80.0,
    ambiguity_margin: float = 5.0,
) -> tuple[
    str | None,
    float,
    dict[str, float] | None,
    list[dict[str, object]],
]:
    """Return the accepted match and every scored candidate, sorted by score.

    Critical identifiers that appear in both names must agree. Construction
    noise words are excluded from scoring, and abbreviation expansion happens
    before comparing with Python's standard-library SequenceMatcher.
    """
    dirty_normalizado = _normalizar(dirty_name)
    dirty_limpio = _quitar_ruido(dirty_normalizado)
    if not dirty_limpio:
        return None, 0.0, None, []

    puntajes: list[tuple[str, float, dict[str, float]]] = []
    metricas_candidatas: list[tuple[float, dict[str, float]]] = []
    candidatos: list[dict[str, object]] = []

    for nombre_oficial in known_projects:
        oficial_normalizado = _normalizar(nombre_oficial)
        oficial_limpio = _quitar_ruido(oficial_normalizado)
        if not oficial_limpio:
            continue

        puntaje, metricas = _comparar_proyectos(
            dirty_name,
            nombre_oficial,
        )
        metricas_candidatas.append((puntaje, metricas))
        candidatos.append({
            "name": nombre_oficial,
            "confidence_score": puntaje,
            "metrics": metricas,
        })
        if not _hay_conflicto_critico(dirty_normalizado, oficial_normalizado):
            puntajes.append((nombre_oficial, puntaje, metricas))

    candidatos.sort(
        key=lambda candidato: candidato["confidence_score"],
        reverse=True,
    )
    if not puntajes:
        metricas = max(metricas_candidatas, key=lambda item: item[0])[1] if metricas_candidatas else None
        return None, 0.0, metricas, candidatos

    puntajes.sort(key=lambda candidato: candidato[1], reverse=True)
    mejor_nombre, mejor_puntaje, mejores_metricas = puntajes[0]
    if mejor_puntaje < threshold:
        return None, mejor_puntaje, mejores_metricas, candidatos

    segundo_nombre, segundo_puntaje = next(
        (
            (nombre, puntaje)
            for nombre, puntaje, _ in puntajes[1:]
            if nombre != mejor_nombre
        ),
        (None, 0.0),
    )
    if (
        segundo_nombre is not None
        and segundo_puntaje >= threshold
        and mejor_puntaje - segundo_puntaje < ambiguity_margin
    ):
        return None, mejor_puntaje, mejores_metricas, candidatos

    return mejor_nombre, mejor_puntaje, mejores_metricas, candidatos


def match_project(
    dirty_name: str,
    known_projects: list[str],
    threshold: float = 80.0,
    ambiguity_margin: float = 5.0,
) -> tuple[str | None, float]:
    best_match, confidence_score, _, _ = match_project_with_metrics(
        dirty_name,
        known_projects,
        threshold=threshold,
        ambiguity_margin=ambiguity_margin,
    )
    return best_match, confidence_score


if __name__ == "__main__":
    print(match_project(
        "1200 Main St Project",
        ["1200 Main Street Renovation"],
    ))
    print(match_project(
        "1200 Main St Phase 1",
        ["1200 Main Street Phase 2"],
    ))