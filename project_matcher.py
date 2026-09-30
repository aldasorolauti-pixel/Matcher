"""
Project name matcher: deterministic, pure Python, no AI, no third-party libs.

Uso:
    from project_matcher import match_best
    r = match_best("2460 North Australian", ["2460 N Australian Ave", "Cedar Ridge Apts"])
    r.match      -> "2460 N Australian Ave"  (o None si se niega a adivinar)
    r.score      -> 0.0 .. 1.0
    r.reason     -> texto explicando la decision (util para logs/auditoria)

Como funciona (3 capas):
  1. NORMALIZACION: minusculas, sin puntuacion, abreviaturas expandidas
     (N->north, Ave->avenue, Bldg->building, Ph 2 -> phase 2, "3rd" -> "third"...).
  2. IDENTIFICADORES DUROS (vetos): numero de calle, job number (24-011),
     fase/edificio/suite, direccion (N/S/E/W), tipo de calle (St/Ave), alcance
     (renovation/addition...). Si AMBOS nombres tienen el mismo tipo de
     identificador y son DISTINTOS -> son proyectos distintos, score 0. Sin
     importar cuanto se parezca el resto del texto. Esto es lo que evita
     "Phase 1" vs "Phase 2".
  3. SIMILITUD SUAVE: coeficiente Dice ponderado sobre tokens, con match difuso
     por distancia de edicion (Damerau-Levenshtein) para tolerar typos.
     Los tokens genericos (street, school, building...) pesan poco; los
     distintivos (australian, riverside) pesan mucho.

Si falta informacion en UN solo lado (ej. uno tiene fase y el otro no), no es
un veto pero si una penalizacion: no sabemos si es el mismo proyecto.

UMBRAL (THRESHOLD = 0.80) - justificacion
-----------------------------------------
* El costo de error es asimetrico. Un falso positivo (unir dos proyectos
  distintos) mete horas/facturas de un proyecto en otro SIN que nadie se
  entere: "confiado y equivocado". Un falso negativo (decir "no se") es
  visible: cae a una cola de revision humana. Por eso el umbral se pone alto.
* Empirico: el test `test_threshold_sweep` barre umbrales de 0.50 a 0.95
  sobre los 50+ pares etiquetados. Resultado observado (ver salida al correr
  el test con -v o el script): todos los matches legitimos puntuan >= ~0.87 y
  el peor near-miss puntua 0.75 (fase faltante en un solo lado). Hay un
  "valle" vacio entre 0.75 y ~0.87; 0.80 esta en el medio, con ~0.05 de margen
  de cada lado. Bajar a 0.70 empieza a aceptar near-misses (falsos positivos);
  subir a 0.90 empieza a perder matches legitimos con abreviaturas + typos.
* Las penalizaciones (fase faltante = -0.25) estan calibradas para que un
  nombre identico pero con informacion de fase en un solo lado caiga a 0.75,
  o sea, justo debajo del umbral: se rechaza.
* Ademas hay una regla de AMBIGUEDAD: si el segundo mejor candidato queda a
  menos de 0.05 del primero (y tambien supera el umbral), no se elige ninguno.
* Limitacion honesta: 40-50 pares inventados no son una muestra de
  produccion. Antes de fiarse del 0.80 hay que re-correr el barrido con pares
  reales (anonimizados) y ajustar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

THRESHOLD = 0.80
AMBIGUITY_MARGIN = 0.05

# --------------------------------------------------------------------------
# Vocabulario
# --------------------------------------------------------------------------

# Como tratar las etapas de diseno (SD/DD/CD/CA). Es una decision de NEGOCIO:
#   "distinct": "Escuela - SD" y "Escuela - CD" se consideran registros distintos (conservador).
#   "ignore":   la etapa de diseno se descarta y ambos nombres se consideran el mismo proyecto.
# Debe confirmarlo alguien de finanzas: depende de como facturen/registren las horas.
DESIGN_STAGE_MODE = "distinct"

DIRECTIONS = {"north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"}
STREET_TYPES = {
    "street", "avenue", "road", "boulevard", "drive", "lane", "court", "place",
    "highway", "parkway", "circle", "terrace", "way", "trail", "plaza",
    "expressway", "freeway",
}
SCOPE_WORDS = {"renovation", "addition", "expansion", "demolition", "ti", "restoration",
               "replacement", "rehabilitation", "repair", "upgrade", "conversion",
               "newconstruction"}
GENERIC_WORDS = STREET_TYPES | {"school", "building", "center", "office", "the"}
NOISE_WORDS = {"project", "projects", "improvements", "improvement", "and", "of", "at",
               "llc", "inc", "co", "new"}

ABBREV = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
    "ave": "avenue", "av": "avenue", "st": "street", "str": "street",
    "blvd": "boulevard", "rd": "road", "dr": "drive", "ln": "lane",
    "ct": "court", "pl": "place", "hwy": "highway", "pkwy": "parkway",
    "cir": "circle", "ter": "terrace", "wy": "way", "trl": "trail", "plz": "plaza",
    "expy": "expressway", "fwy": "freeway",
    "apts": "apartments", "condos": "condominiums", "condo": "condominiums",
    "elem": "elementary", "sch": "school", "ctr": "center",
    "hosp": "hospital", "mt": "mount", "ft": "fort",
    "reno": "renovation", "renovations": "renovation", "remodel": "renovation",
    "remodeling": "renovation", "renov": "renovation",
    "add": "addition", "demo": "demolition", "rehab": "rehabilitation",
    "upgrades": "upgrade", "repairs": "repair",
}
MULTI_WORD = {"hs": ["high", "school"], "ms": ["middle", "school"]}

ORDINALS = {
    "1st": "first", "2nd": "second", "3rd": "third", "4th": "fourth",
    "5th": "fifth", "6th": "sixth", "7th": "seventh", "8th": "eighth",
    "9th": "ninth", "10th": "tenth", "11th": "eleventh", "12th": "twelfth",
}
ROMAN = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5"}
WORDNUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
           "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}

DESIGNATOR_KIND = {
    "phase": "phase", "ph": "phase", "fase": "phase", "stage": "phase",
    "building": "building", "bldg": "building",
    "suite": "suite", "ste": "suite", "unit": "suite", "apt": "suite", "apartment": "suite",
    "tower": "tower", "wing": "wing", "lot": "lot", "block": "block",
    "floor": "floor", "level": "floor", "zone": "zone",
    "package": "package", "pkg": "package", "option": "option", "alt": "alt",
}

# Penalizacion cuando un identificador esta en un solo lado (default 0.25).
ONE_SIDED_PENALTY = {"subjob": 0.10, "permit": 0.05, "apn": 0.05, "bid": 0.05, "contract": 0.05}

STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV "
             "NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split())

_ID = r"(\d+[a-z]?|one|two|three|four|five|six|seven|eight|nine|ten|iii|ii|iv|i|v|[a-z])"
_DESIG_RE = re.compile(
    r"\b(" + "|".join(sorted(DESIGNATOR_KIND, key=len, reverse=True)) + r")(?:\b|(?=\d))[\s#.:-]*" + _ID + r"\b"
)
_JOB_RE = re.compile(
    r"\b(?:(?:job|proj(?:ect)?|p)[\s#.:-]*)?(\d{2}|\d{4})[-.](\d{3,4})(?:[.-]([a-z]|\d{1,2}))?(?!\w)"
)
_REF_RE = re.compile(
    r"\b(permit|apn|rfp|rfq|itb|bid|contract)\b\.?[\s]*(?:no\.?|number|#|:)?[\s]*([a-z0-9-]*\d[a-z0-9-]*)"
)
_REF_KIND = {"permit": "permit", "apn": "apn", "rfp": "bid", "rfq": "bid", "itb": "bid",
             "bid": "bid", "contract": "contract"}
ROUTES = [  # (regex, familia); orden importa: US antes que highway generico
    (re.compile(r"\bu\.?s\.?[\s-]*(?:highway\s+|hwy\s+|route\s+)?(\d{1,3})\b"), "us"),
    (re.compile(r"\binterstate[\s-]*(\d{1,3})\b|\bi-(\d{1,3})\b"), "i"),
    (re.compile(r"\b(?:sr|rt|route|state\s+route|state\s+highway)[\s.-]*(\d{1,4})\b"), "sr"),
    (re.compile(r"\b(?:cr|county\s+road)[\s-]*(\d{1,4})\b"), "cr"),
    (re.compile(r"\bfm[\s-]*(\d{1,4})\b"), "fm"),
    (re.compile(r"\b(?:hwy|highway)[\s.-]*(\d{1,4})\b"), "hwy"),
]
_TI_RE = re.compile(r"\btenant\s+improvements?\b")
_NEWCON_RE = re.compile(r"\bnew\s+construction\b")
_STAGE_SPELLED = [(re.compile(r"\bschematic\s+design\b"), "sd"),
                  (re.compile(r"\bdesign\s+development\b"), "dd"),
                  (re.compile(r"\bconstruction\s+documents\b"), "cd"),
                  (re.compile(r"\bconstruction\s+administration\b"), "ca")]


# --------------------------------------------------------------------------
# Distancia de edicion (Damerau-Levenshtein, variante OSA; implementada a mano)
# --------------------------------------------------------------------------

def edit_distance(a: str, b: str) -> int:
    la, lb = len(a), len(b)
    d = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        d[i][0] = i
    for j in range(lb + 1):
        d[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)  # transposicion
    return d[la][lb]


def similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    longest = max(len(a), len(b))
    return 1.0 - edit_distance(a, b) / longest if longest else 1.0


# --------------------------------------------------------------------------
# Normalizacion / parseo
# --------------------------------------------------------------------------

@dataclass
class Parsed:
    raw: str
    job: Optional[str] = None
    street_no: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    city: Optional[str] = None
    directions: frozenset = frozenset()
    street_types: frozenset = frozenset()
    scope: frozenset = frozenset()
    designators: dict = field(default_factory=dict)  # {"phase": "2", "route": "i95", ...}
    tokens: list = field(default_factory=list)       # [(token, weight)]


def _extract_location(name: str):
    """Saca ', Austin, TX 78701' del final (solo si el estado va en MAYUSCULAS)."""
    segs = [x.strip() for x in name.split(",")]
    state = zip_ = city = None
    if len(segs) > 1:
        m = re.fullmatch(r"([A-Z]{2})(?:\s+(\d{5})(?:-\d{4})?)?", segs[-1])
        if m and m.group(1) in STATES:
            state, zip_ = m.group(1).lower(), m.group(2)
            segs.pop()
            if (len(segs) > 1 and re.fullmatch(r"[A-Za-z .'-]{2,30}", segs[-1])
                    and len(segs[-1].split()) <= 3
                    and not _DESIG_RE.search(segs[-1].lower())):
                city = re.sub(r"[^a-z]+", " ", segs.pop().lower()).strip()
    else:
        m = re.search(r"\b([A-Z]{2})\s+(\d{5})(?:-\d{4})?\b", name)
        if m and m.group(1) in STATES:
            state, zip_ = m.group(1).lower(), m.group(2)
            name = name[:m.start()] + " " + name[m.end():]
            segs = [name]
    return ", ".join(segs), state, zip_, city


def _valid_job(year: str, seq: str) -> bool:
    """Descarta rangos de direccion tipo '1200-1210'."""
    if len(year) == 4:
        return 1990 <= int(year) <= 2099 and int(seq) < int(year)
    return True


def parse(name: str) -> Parsed:
    p = Parsed(raw=name)
    text, p.state, p.zip, p.city = _extract_location(name)

    # Etapas de diseno abreviadas (solo MAYUSCULAS, para no confundir con estados: "CA", "SD"...)
    stages: list[str] = []

    def _stage(m: re.Match) -> str:
        stages.append(m.group(1).lower())
        return " "

    text = re.sub(r"(?<![A-Za-z0-9])(SD|DD|CD)(?![A-Za-z0-9])", _stage, text)

    text = text.lower().replace("&", " and ")
    text = re.sub(r"[’'`]", "", text)  # mary's -> marys

    for rx, sid in _STAGE_SPELLED:
        if rx.search(text):
            stages.append(sid)
            text = rx.sub(" ", text)
    if stages:
        p.designators["design_stage"] = "+".join(sorted(set(stages)))

    # Referencias legales: permit / APN / bid / contract (antes del job number: "RFP 2024-045")
    def _ref(m: re.Match) -> str:
        p.designators[_REF_KIND[m.group(1)]] = re.sub(r"[^a-z0-9]", "", m.group(2))
        return " "

    text = _REF_RE.sub(_ref, text)

    # Rutas numeradas
    for rx, fam in ROUTES:
        m = rx.search(text)
        if m:
            num = next(g for g in m.groups() if g)
            p.designators["route"] = f"{fam}{num}"
            text = text[:m.start()] + " " + text[m.end():]

    # Job number: 24-011, 2024-011, 2024.011, P-24-011, 24-011.02, 24-011-A
    for m in _JOB_RE.finditer(text):
        if _valid_job(m.group(1), m.group(2)):
            p.job = f"{m.group(1)[-2:]}-{m.group(2)}"
            if m.group(3):
                p.designators["subjob"] = m.group(3)
            text = text[:m.start()] + " " + text[m.end():]
            break

    text = _TI_RE.sub(" ti ", text)
    text = _NEWCON_RE.sub(" newconstruction ", text)

    def _desig(m2: re.Match) -> str:
        kind = DESIGNATOR_KIND[m2.group(1)]
        ident = m2.group(2)
        ident = WORDNUM.get(ident, ROMAN.get(ident, ident))
        p.designators[kind] = ident
        return " "

    text = _DESIG_RE.sub(_desig, text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    raw_tokens = text.split()

    tokens: list[str] = []
    for i, t in enumerate(raw_tokens):
        t = ORDINALS.get(t, t)
        # "St" = Saint si va al inicio o justo despues de un numero ("500 St Charles Ave")
        if t == "st" and (i == 0 or raw_tokens[i - 1].isdigit()):
            tokens.append("saint")
            continue
        if t in MULTI_WORD:
            tokens.extend(MULTI_WORD[t])
            continue
        tokens.append(ABBREV.get(t, t))

    # "north east" -> "northeast"
    merged, i = [], 0
    while i < len(tokens):
        if tokens[i] in ("north", "south") and i + 1 < len(tokens) and tokens[i + 1] in ("east", "west"):
            merged.append(tokens[i] + tokens[i + 1])
            i += 2
        else:
            merged.append(tokens[i])
            i += 1
    tokens = merged

    if tokens and tokens[0].isdigit():
        p.street_no = tokens.pop(0)

    dirs, types, scope, weighted = set(), set(), set(), []
    for t in tokens:
        if t in NOISE_WORDS:
            continue
        if t in DIRECTIONS:
            dirs.add(t)
        elif t in SCOPE_WORDS:
            scope.add(t)
        elif t in STREET_TYPES:
            types.add(t)
            weighted.append((t, 0.4))
        elif t in GENERIC_WORDS:
            weighted.append((t, 0.4))
        elif any(ch.isdigit() for ch in t):
            weighted.append((t, 2.0))  # numeros sueltos ("station 4") discriminan mucho
        else:
            weighted.append((t, 1.0))
    p.directions, p.street_types, p.scope = frozenset(dirs), frozenset(types), frozenset(scope)
    p.tokens = weighted
    return p


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

@dataclass
class Score:
    score: float
    reason: str


def _weighted_dice(a: list, b: list) -> float:
    total_a = sum(w for _, w in a)
    total_b = sum(w for _, w in b)
    if total_a + total_b == 0:
        return 0.0
    used, matched = set(), 0.0
    for tok, w in sorted(a, key=lambda x: -x[1]):
        best_j, best_s = None, 0.0
        for j, (tok2, w2) in enumerate(b):
            if j in used:
                continue
            if tok == tok2:
                s = 1.0
            elif (len(tok) >= 5 and len(tok2) >= 5
                  and not any(c.isdigit() for c in tok + tok2)):
                s = similarity(tok, tok2)
                if s < 0.8:
                    s = 0.0
            else:
                s = 0.0
            if s > best_s:
                best_j, best_s = j, s
        if best_j is not None:
            used.add(best_j)
            matched += min(w, b[best_j][1]) * best_s
    return 2 * matched / (total_a + total_b)


def score_pair(name_a: str, name_b: str) -> Score:
    a, b = parse(name_a), parse(name_b)
    if DESIGN_STAGE_MODE == "ignore":
        a.designators.pop("design_stage", None)
        b.designators.pop("design_stage", None)

    # --- vetos: identificadores duros en conflicto -------------------------
    if a.job and b.job and a.job != b.job:
        return Score(0.0, f"veto: job numbers distintos ({a.job} vs {b.job})")
    if a.street_no and b.street_no and a.street_no != b.street_no:
        return Score(0.0, f"veto: numero de calle distinto ({a.street_no} vs {b.street_no})")
    for f, label in (("state", "estado"), ("zip", "ZIP"), ("city", "ciudad")):
        va, vb = getattr(a, f), getattr(b, f)
        if va and vb and va != vb:
            return Score(0.0, f"veto: {label} distinto ({va} vs {vb})")
    for kind in a.designators.keys() & b.designators.keys():
        if a.designators[kind] != b.designators[kind]:
            return Score(0.0, f"veto: {kind} distinta ({a.designators[kind]} vs {b.designators[kind]})")
    if a.directions and b.directions and a.directions != b.directions:
        return Score(0.0, "veto: direccion cardinal distinta")
    if a.street_types and b.street_types and a.street_types != b.street_types:
        return Score(0.0, "veto: tipo de calle distinto")
    if a.scope and b.scope and a.scope != b.scope:
        return Score(0.0, "veto: alcance distinto (renovation vs addition, etc.)")

    # --- similitud suave ---------------------------------------------------
    # Un tipo de calle presente en un solo lado es informacion ausente, no discrepancia.
    ta, tb = a.tokens, b.tokens
    if a.street_types and not b.street_types:
        ta = [(t, w) for t, w in ta if t not in STREET_TYPES]
    elif b.street_types and not a.street_types:
        tb = [(t, w) for t, w in tb if t not in STREET_TYPES]
    score = _weighted_dice(ta, tb)
    notes = [f"dice={score:.2f}"]

    # --- informacion presente en un solo lado: penalizacion ---------------
    def one_sided(x, y):  # exactamente uno tiene el dato
        return bool(x) != bool(y)

    for kind in set(a.designators) ^ set(b.designators):
        pen = ONE_SIDED_PENALTY.get(kind, 0.25)
        score -= pen
        notes.append(f"-{pen:.2f} {kind} en un solo lado")
    for f in ("state", "zip", "city"):
        if one_sided(getattr(a, f), getattr(b, f)):
            score -= 0.02
    if one_sided(a.job, b.job):
        score -= 0.02
    if one_sided(a.street_no, b.street_no):
        score -= 0.02
    if one_sided(a.directions, b.directions):
        score -= 0.02
    if one_sided(a.street_types, b.street_types):
        score -= 0.02
    if one_sided(a.scope, b.scope):
        score -= 0.05

    # --- job number identico en ambos: evidencia fuerte -------------------
    if a.job and a.job == b.job:
        score += 0.15
        notes.append("+0.15 mismo job number")

    return Score(max(0.0, min(1.0, round(score, 4))), "; ".join(notes))


# --------------------------------------------------------------------------
# API publica
# --------------------------------------------------------------------------

@dataclass
class MatchResult:
    query: str
    match: Optional[str]      # None => "no se"
    score: float              # confianza del mejor candidato (aunque se rechace)
    best_candidate: Optional[str]
    reason: str


def match_best(name: str, candidates: list[str],
               threshold: float = THRESHOLD,
               margin: float = AMBIGUITY_MARGIN) -> MatchResult:
    if not candidates or not name or not name.strip():
        return MatchResult(name, None, 0.0, None, "sin entrada o sin candidatos")

    scored = sorted(((score_pair(name, c), c) for c in candidates),
                    key=lambda x: -x[0].score)
    best, best_name = scored[0]

    if best.score < threshold:
        return MatchResult(name, None, best.score, best_name,
                           f"rechazado: {best.score:.2f} < umbral {threshold:.2f} ({best.reason})")

    if len(scored) > 1:
        second, second_name = scored[1]
        if second.score >= threshold and best.score - second.score < margin:
            return MatchResult(name, None, best.score, best_name,
                               f"rechazado por ambiguedad: '{best_name}' ({best.score:.2f}) vs "
                               f"'{second_name}' ({second.score:.2f})")

    return MatchResult(name, best_name, best.score, best_name, f"match ({best.reason})")
