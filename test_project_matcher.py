"""
Tests del matcher. Correr:  python -m unittest test_project_matcher -v
Barrido de umbrales:        python test_project_matcher.py
"""
import unittest

from project_matcher import THRESHOLD, match_best, parse, score_pair

# (a, b, debe_matchear, por_que)
MATCHES = [
    ("2460 N Australian Ave", "2460 North Australian", "caso del brief: abreviatura + calle incompleta"),
    ("2460 N Australian Ave", "24-011 Australian Ave Renovation", "caso del brief: job number vs numero de calle"),
    ("123 Main St", "123 Main Street", "St/Street"),
    ("123 Main St.", "123 MAIN STREET", "puntuacion y mayusculas"),
    ("500 W. Colorado Blvd", "500 West Colorado Boulevard", "W/West + Blvd"),
    ("24-015 Riverside Elementary School", "Riverside Elementary School", "job number solo de un lado"),
    ("24-015 Riverside Elementary", "Riverside Elementary School", "palabra generica 'school' faltante"),
    ("Riverside Elementary School Ph 2", "Riverside Elem. School Phase 2", "Ph 2 / Elem."),
    ("1800 S Broadway Ste 200 TI", "1800 South Broadway Suite 200 Tenant Improvement", "TI = tenant improvement"),
    ("Mercy Hospital - Bldg B Expansion", "Mercy Hospital Building B Expansion", "Bldg B"),
    ("Cedar Ridge Apartments", "Cedar Ridge Apts", "Apts"),
    ("Cedar Ridge Apartments", "Cedar Rdige Apartments", "typo por transposicion"),
    ("2460 N Australian Ave", "2460 N Austrailian Ave", "typo en el nombre distintivo"),
    ("24-011 Australian Ave Reno", "2460 N Australian Ave Renovation", "Reno = renovation"),
    ("St. Mary's Medical Center", "Saint Marys Medical Center", "St = Saint, apostrofe"),
    ("Harbor View Condos Phase 1", "Harbor View Condominiums Ph. 1", "condos + Ph."),
    ("Oakwood Dr Bridge Replacement", "Oakwood Drive Bridge Replacement", "Dr/Drive"),
    ("  1200 e. main   street  ", "1200 East Main Street", "espacios raros"),
    ("Lincoln High School Gym Addition", "Lincoln HS Gym Addition", "HS = high school"),
    ("Sunset Blvd Streetscape", "Sunset Boulevard Streetscape Improvements", "palabra de ruido 'improvements'"),
    ("Riverside Elementary School", "24-015 Riverside Elem Sch", "Elem Sch"),
    ("1010 N. Wabash Ave. Lobby Remodel", "1010 North Wabash Avenue Lobby Renovation", "remodel = renovation"),
    ("Pine St Fire Station 4", "Pine Street Fire Station #4", "numero de estacion con #"),
    ("Willow Creek Trail Phase II", "Willow Creek Trail Ph 2", "romano vs arabigo"),
    ("3rd Ave Parking Garage", "Third Avenue Parking Garage", "ordinal"),
    ("2460 N. Australian Ave. - Renovation", "2460 N Australian Ave Renovation", "guion y puntos"),
    ("24-011 Australian Ave Renovation", "24-011 Australian Avenue Reno", "mismo job number"),
    # --- formatos extendidos ---
    ("Riverside Elementary School Phase One", "Riverside Elem Sch Ph 1", "numero en palabras"),
    ("Riverside Elementary School Ph2", "Riverside Elementary School Phase 2", "Ph2 pegado"),
    ("Harbor View Condos Phase 1A", "Harbor View Condominiums Ph. 1A", "fase con letra"),
    ("Harbor View Condos Stage 2", "Harbor View Condos Phase 2", "stage = phase"),
    ("100 Main St NW", "100 Northwest Main Street", "direccional compuesto"),
    ("1500 NE Broadway Blvd", "1500 Northeast Broadway Boulevard", "NE / Northeast"),
    ("2024-011 Australian Ave Renovation", "24-011 Australian Avenue Renovation", "job number con anio de 4 digitos"),
    ("24-011 Australian Ave", "2024.011 Australian Avenue", "job number con punto"),
    ("P-24-011 Australian Ave Renovation", "24-011 Australian Ave Renovation", "job number con prefijo P-"),
    ("24-011.02 Australian Ave", "24-011.02 Australian Avenue Reno", "mismo sub-job"),
    ("Riverside Elementary School - SD", "Riverside Elementary School Schematic Design", "etapa SD"),
    ("Riverside Elementary School CD", "Riverside Elem Sch Construction Documents", "etapa CD"),
    ("2460 N Australian Ave, Austin, TX 78701", "2460 North Australian Avenue", "ciudad/estado/ZIP en un solo lado"),
    ("2460 N Australian Ave, Austin, TX", "2460 N Australian Ave, Austin, TX 78701", "ZIP en un solo lado"),
    ("I-95 Bridge Rehabilitation", "Interstate 95 Bridge Rehab", "interestatal"),
    ("US-101 Widening", "US Highway 101 Widening", "ruta US"),
    ("Hwy 61 Bridge Replacement", "Highway 61 Bridge Replacement", "Hwy/Highway"),
    ("State Route 99 Overpass", "SR-99 Overpass", "ruta estatal"),
    ("Lakeside Clinic Permit No. 2024-0456", "Lakeside Clinic Permit #2024-0456", "numero de permiso"),
    ("Fire Station 12 RFP 2024-045", "Fire Station 12 Bid No. 2024-045", "RFP = bid"),
    ("Elm St Parcel APN 123-456-789", "Elm Street Parcel APN 123456789", "APN con y sin guiones"),
    ("Oak Plaza Tower 2", "Oak Plaza Tower Two", "torre en palabras"),
    ("Willow Creek Trl Phase 2", "Willow Creek Trail Ph 2", "Trl = trail"),
]

NEAR_MISSES = [
    ("123 Main St - Phase 1", "123 Main St - Phase 2", "fases distintas"),
    ("2460 N Australian Ave", "2460 S Australian Ave", "norte vs sur"),
    ("2460 N Australian Ave", "2640 N Australian Ave", "digitos transpuestos en el numero de calle"),
    ("24-011 Australian Ave Renovation", "24-012 Australian Ave Renovation", "job numbers consecutivos"),
    ("123 Main St", "123 Main Ave", "Street vs Avenue"),
    ("1800 S Broadway Ste 200", "1800 S Broadway Ste 300", "suites distintas del mismo edificio"),
    ("Mercy Hospital Bldg A Expansion", "Mercy Hospital Bldg B Expansion", "edificios distintos"),
    ("Riverside Elementary School", "Riverside Middle School", "escuelas distintas, misma calle/nombre"),
    ("123 Main St Renovation", "123 Main St Addition", "mismo sitio, alcance distinto"),
    ("Oak Street Elementary School", "Oak Street", "uno contiene al otro pero no es lo mismo"),
    ("Cedar Ridge Apartments", "Cedar Ridge Townhomes", "mismo desarrollo, producto distinto"),
    ("Harbor View Condos Phase 1", "Harbor View Condos", "fase solo de un lado: no se sabe"),
    ("Lincoln High School Gym Addition", "Lincoln High School Field House Addition", "otro edificio del mismo campus"),
    ("Pine St Fire Station 4", "Pine St Fire Station 5", "estacion 4 vs 5"),
    ("Sunset Blvd Streetscape", "Sunset Blvd Bridge Replacement", "misma calle, obra distinta"),
    ("500 W Colorado Blvd", "500 W Colorado St", "tipo de calle distinto"),
    ("1010 N Wabash Ave Lobby Remodel", "1010 N Wabash Ave Roof Replacement", "mismo edificio, trabajo distinto"),
    ("Willow Creek Trail", "Willow Creek Golf Course", "mismo prefijo"),
    ("24-015 Riverside Elementary School", "24-051 Riverside Elementary School", "job numbers transpuestos"),
    ("St. Mary's Medical Center", "St. Luke's Medical Center", "santos distintos"),
    ("Harbor View Condos Phase 1", "Harbor View Condos Phase 3", "fase 1 vs 3"),
    ("Oakwood Dr Bridge Replacement", "Oakwood Dr Bridge Rehabilitation", "obra distinta"),
    ("Lakeside Medical Office Building", "Lakeside Medical Office Building Parking Structure", "estacionamiento aparte"),
    ("Cedar Ridge Apartments", "Cedar Grove Apartments", "nombre distintivo distinto"),
    ("Downtown Library Renovation", "Downtown Library Addition", "alcance distinto"),
    ("Maple St Townhomes Phase A", "Maple St Townhomes Phase B", "fase A vs B"),
    ("2460 N Australian Ave", "2460 N Australia Blvd", "calle distinta parecida"),
    # --- formatos extendidos ---
    ("100 Main St NW", "100 Main St SE", "NW vs SE"),
    ("100 Main St NW", "100 Main St NE", "NW vs NE"),
    ("1500 NE Broadway Blvd", "1500 SE Broadway Blvd", "NE vs SE"),
    ("24-011.01 Australian Ave", "24-011.02 Australian Ave", "sub-jobs distintos"),
    ("2024-011 Australian Ave", "2024-012 Australian Ave", "job numbers de 4 digitos"),
    ("24-011 Australian Ave", "25-011 Australian Ave", "misma secuencia, otro anio"),
    ("Riverside Elementary School SD", "Riverside Elementary School CD", "etapas de diseno distintas"),
    ("Riverside Elementary School", "Riverside Elementary School - SD", "etapa de diseno solo de un lado"),
    ("Riverside Elementary School Ph2", "Riverside Elementary School Ph3", "Ph2 vs Ph3"),
    ("2460 N Australian Ave, Austin, TX", "2460 N Australian Ave, Dallas, TX", "misma calle, otra ciudad"),
    ("2460 N Australian Ave, Austin, TX 78701", "2460 N Australian Ave, Austin, TX 78702", "ZIP distinto"),
    ("I-95 Bridge Rehabilitation", "I-91 Bridge Rehabilitation", "interestatales distintas"),
    ("Hwy 61 Bridge Replacement", "Hwy 62 Bridge Replacement", "rutas distintas"),
    ("Lakeside Clinic Permit No. 2024-0456", "Lakeside Clinic Permit No. 2024-0457", "permisos consecutivos"),
    ("Fire Station 12 RFP 2024-045", "Fire Station 12 RFP 2024-046", "licitaciones consecutivas"),
    ("Elm St Parcel APN 123-456-789", "Elm St Parcel APN 123-456-790", "APN consecutivo"),
    ("Oak Plaza Tower 2", "Oak Plaza Tower 3", "torres distintas"),
    ("Willow Creek Trail Phase 2", "Willow Creek Road Phase 2", "trail vs road"),
    ("Harbor View Condos Stage 1", "Harbor View Condos Phase 2", "stage 1 vs phase 2"),
    ("Riverside Elementary School Floor 2 TI", "Riverside Elementary School Floor 3 TI", "pisos distintos"),
    ("Cedar Ridge Apts Apt 4B", "Cedar Ridge Apts Apt 4C", "unidades distintas"),
    ("Harbor View Condos Option A", "Harbor View Condos Option B", "opciones distintas"),
    ("1200-1210 Main St", "1200-1220 Main St", "rango de direcciones (no es job number)"),
]

CATALOG = [
    "2460 N Australian Ave",
    "Riverside Elementary School",
    "Cedar Ridge Apartments",
    "Mercy Hospital Bldg B Expansion",
    "Harbor View Condos Phase 1",
    "Harbor View Condos Phase 2",
]


class TestPairs(unittest.TestCase):
    def test_enough_pairs(self):
        self.assertGreaterEqual(len(MATCHES) + len(NEAR_MISSES), 40)

    def test_matches_are_accepted(self):
        for a, b, why in MATCHES:
            for x, y in ((a, b), (b, a)):  # simetria
                with self.subTest(a=x, b=y, why=why):
                    r = match_best(x, [y])
                    self.assertEqual(r.match, y, f"{why} -> score {r.score}: {r.reason}")

    def test_near_misses_are_refused(self):
        for a, b, why in NEAR_MISSES:
            for x, y in ((a, b), (b, a)):
                with self.subTest(a=x, b=y, why=why):
                    r = match_best(x, [y])
                    self.assertIsNone(r.match, f"{why} -> score {r.score}: {r.reason}")

    def test_threshold_has_safety_margin(self):
        """El umbral debe estar en un valle: >=0.04 de margen a cada lado."""
        low_match = min(score_pair(a, b).score for a, b, _ in MATCHES)
        high_miss = max(score_pair(a, b).score for a, b, _ in NEAR_MISSES)
        self.assertGreaterEqual(low_match - THRESHOLD, 0.04, f"match mas bajo: {low_match}")
        self.assertGreaterEqual(THRESHOLD - high_miss, 0.04, f"near-miss mas alto: {high_miss}")


class TestCatalog(unittest.TestCase):
    def test_picks_correct_project(self):
        self.assertEqual(match_best("2460 North Australian", CATALOG).match, "2460 N Australian Ave")
        self.assertEqual(match_best("24-015 Riverside Elem", CATALOG).match, "Riverside Elementary School")
        self.assertEqual(match_best("Harbor View Condominiums Ph 2", CATALOG).match, "Harbor View Condos Phase 2")

    def test_refuses_unknown(self):
        r = match_best("Grand Central Terminal Upgrade", CATALOG)
        self.assertIsNone(r.match)

    def test_refuses_when_phase_missing(self):
        # Hay Fase 1 y Fase 2 en el catalogo: adivinar seria un coin flip.
        self.assertIsNone(match_best("Harbor View Condos", CATALOG).match)

    def test_refuses_ambiguous_duplicates(self):
        dup = ["Main Street Lofts", "Main St Lofts"]
        r = match_best("Main Street Lofts", dup)
        self.assertIsNone(r.match)
        self.assertIn("ambiguedad", r.reason)

    def test_empty_inputs(self):
        self.assertIsNone(match_best("", CATALOG).match)
        self.assertIsNone(match_best("2460 N Australian Ave", []).match)


class TestParsing(unittest.TestCase):
    """Si un formato no se DETECTA, el veto no se dispara y el error es silencioso."""

    def test_job_number_formats(self):
        for text in ["24-011 X", "2024-011 X", "2024.011 X", "P-24-011 X", "Job #24-011 X", "X 24-011"]:
            with self.subTest(text=text):
                self.assertEqual(parse(text).job, "24-011")

    def test_subjob(self):
        self.assertEqual(parse("24-011.02 X").designators.get("subjob"), "02")
        self.assertEqual(parse("24-011-A X").designators.get("subjob"), "a")

    def test_address_range_is_not_a_job_number(self):
        self.assertIsNone(parse("1200-1210 Main St").job)

    def test_designators(self):
        cases = {
            "X Phase II": ("phase", "2"), "X Ph. 3": ("phase", "3"), "X Ph3": ("phase", "3"),
            "X Fase 1": ("phase", "1"), "X Bldg #B": ("building", "b"), "X Ste 200": ("suite", "200"),
            "X Tower Two": ("tower", "2"), "X Wing C": ("wing", "c"), "X Lot 14": ("lot", "14"),
            "X Floor 3": ("floor", "3"), "X Option A": ("option", "a"),
        }
        for text, (kind, ident) in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse(text).designators.get(kind), ident)

    def test_routes(self):
        cases = {"I-95 X": "i95", "Interstate 95 X": "i95", "US-101 X": "us101",
                 "US Highway 101 X": "us101", "SR 99 X": "sr99", "State Route 99 X": "sr99",
                 "Hwy 61 X": "hwy61", "County Road 12 X": "cr12"}
        for text, rid in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse(text).designators.get("route"), rid)

    def test_legal_references(self):
        self.assertEqual(parse("X Permit No. 2024-0456").designators.get("permit"), "20240456")
        self.assertEqual(parse("X APN 123-456-789").designators.get("apn"), "123456789")
        self.assertEqual(parse("X RFP 2024-045").designators.get("bid"), "2024045")
        self.assertIsNone(parse("X RFP 2024-045").job)  # no confundir con job number

    def test_design_stages(self):
        self.assertEqual(parse("X - SD").designators.get("design_stage"), "sd")
        self.assertEqual(parse("X Design Development").designators.get("design_stage"), "dd")

    def test_state_zip_city(self):
        p = parse("2460 N Australian Ave, Austin, TX 78701")
        self.assertEqual((p.city, p.state, p.zip), ("austin", "tx", "78701"))
        self.assertEqual(p.street_no, "2460")

    def test_lowercase_state_codes_are_not_states(self):
        # "ca" / "sd" en minuscula NO se interpretan como estado ni etapa de diseno
        self.assertIsNone(parse("Harbor, ca").state)
        self.assertNotIn("design_stage", parse("Harbor sd").designators)


def threshold_sweep():
    print(f"{'umbral':>6} | {'falsos +':>8} | {'falsos -':>8}")
    for t in [x / 100 for x in range(50, 100, 5)]:
        fp = sum(score_pair(a, b).score >= t for a, b, _ in NEAR_MISSES)
        fn = sum(score_pair(a, b).score < t for a, b, _ in MATCHES)
        mark = "  <-- elegido" if abs(t - THRESHOLD) < 1e-9 else ""
        print(f"{t:6.2f} | {fp:8d} | {fn:8d}{mark}")
    print("\nMatches, de menor a mayor score:")
    for s, a, b in sorted((score_pair(a, b).score, a, b) for a, b, _ in MATCHES)[:5]:
        print(f"  {s:.2f}  {a!r} ~ {b!r}")
    print("Near-misses, de mayor a menor score:")
    for s, a, b in sorted(((score_pair(a, b).score, a, b) for a, b, _ in NEAR_MISSES), reverse=True)[:5]:
        print(f"  {s:.2f}  {a!r} ~ {b!r}")


if __name__ == "__main__":
    threshold_sweep()
