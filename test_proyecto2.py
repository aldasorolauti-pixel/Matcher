import unittest

from proyecto2 import match_project, match_project_with_metrics


MATCH_CASES = [
    ("2460 N Australian Ave", ["2460 North Australian"], "2460 North Australian"),
    ("24-011 Australian Ave Renovation", ["24-011 Australian Avenue Renovation"], "24-011 Australian Avenue Renovation"),
    ("24-011 2460 Australian Ave", ["2460 Australian Ave"], "2460 Australian Ave"),
    ("2460 North Australian Ave", ["2460 Australian Ave"], "2460 Australian Ave"),
    ("1500 S Broadway", ["1500 South Broadway"], "1500 South Broadway"),
    ("7800 W Sample Rd", ["7800 West Sample Road"], "7800 West Sample Road"),
    ("310 E Main St", ["310 East Main Street"], "310 East Main Street"),
    ("24-011: 2460 North Australian", ["24-011 2460 N Australian"], "24-011 2460 N Australian"),
    ("500 NW 2nd Ave Library", ["500 Northwest 2nd Avenue Library"], "500 Northwest 2nd Avenue Library"),
    ("Bldg 4, 700 Central Blvd", ["Building 4 700 Central Boulevard"], "Building 4 700 Central Boulevard"),
    ("1200 Market St - Renovation", ["1200 Market Street Renovation"], "1200 Market Street Renovation"),
    ("Job 23-104: Westlake Clinic", ["23-104 Westlake Clinic"], "23-104 Westlake Clinic"),
    ("401 Oak Dr Suite 200", ["401 Oak Drive Ste 200"], "401 Oak Drive Ste 200"),
    ("88 County Hwy 6 Bridge Replacement", ["88 County Highway 6 Bridge Replacement"], "88 County Highway 6 Bridge Replacement"),
    ("Project 19-203 North Campus Bldg 2", ["19-203 North Campus Building 2"], "19-203 North Campus Building 2"),
    ("900 S Miami Ave Parking Garage", ["900 South Miami Avenue Parking Garage"], "900 South Miami Avenue Parking Garage"),
    ("Parcel 77 1600 E 8th St", ["77 1600 East 8th Street"], "77 1600 East 8th Street"),
    ("1250 Pine Street", ["1250 Pine Stret"], "1250 Pine Stret"),
    ("220 W Lake Dr Phase 1", ["220 West Lake Drive Phase 1"], "220 West Lake Drive Phase 1"),
    ("Building 3 - 500 NE 4th Street", ["Bldg 3 500 Northeast 4th St"], "Bldg 3 500 Northeast 4th St"),
    ("6300 S Orange Ave Medical Office", ["6300 South Orange Avenue Medical Office"], "6300 South Orange Avenue Medical Office"),
    ("Job 25-008: 90 Harbor Blvd Pier Upgrade", ["25-008 90 Harbor Boulevard Pier Upgrade"], "25-008 90 Harbor Boulevard Pier Upgrade"),
]


NO_MATCH_CASES = [
    ("123 Main St Phase 1", ["123 Main St" ]),
    ("123 Main St Phase 1", ["123 Main St Phase 2"]),
    ("24-011 Australian Ave Renovation", ["24-012 Australian Ave Renovation"]),
    ("1500 North Broadway", ["1500 South Broadway"]),
    ("500 East 8th Street", ["500 West 8th Street"]),
    ("2460 North Australian Ave", ["2461 North Australian Ave"]),
    ("800 Main Street", ["800 Main Street Annex Phase 2"]),
    ("Job 23-104 Westlake Clinic", ["Job 23-105 Westlake Clinic"]),
    ("Building 1 700 Central Blvd", ["Building 2 700 Central Blvd"]),
    ("900 South Miami Avenue Garage", ["900 South Miami Avenue Office"]),
    ("1200 Market Street Phase 3", ["1200 Market Street Phase 4"]),
    ("77 1600 East 8th Street", ["77 1600 West 8th Street"]),
    ("310 East Main Street", ["311 East Main Street"]),
    ("401 Oak Drive Suite 200", ["401 Oak Drive Suite 201"]),
    ("88 County Highway 6 Bridge", ["88 County Highway 9 Bridge"]),
    ("220 West Lake Drive Phase 1", ["220 West Lake Drive Phase 2"]),
    ("6300 South Orange Avenue Medical Office", ["6300 North Orange Avenue Medical Office"]),
    ("25-008 90 Harbor Blvd Pier Upgrade", ["25-009 90 Harbor Blvd Pier Upgrade"]),
    ("500 Northwest 4th Street Library", ["500 Southeast 4th Street Library"]),
    ("1250 Pine Street Renovation", ["1250 Pine Street Demolition"]),
]


class ProjectNameMatcherTests(unittest.TestCase):
    def test_realistic_matches(self):
        self.assertEqual(len(MATCH_CASES), 22)
        for incoming, official_names, expected in MATCH_CASES:
            with self.subTest(incoming=incoming):
                match, score = match_project(incoming, official_names, threshold=82.0)
                self.assertEqual(match, expected)
                self.assertGreaterEqual(score, 82.0)

    def test_near_misses_are_rejected(self):
        self.assertEqual(len(NO_MATCH_CASES), 20)
        for incoming, official_names in NO_MATCH_CASES:
            with self.subTest(incoming=incoming):
                match, _ = match_project(incoming, official_names, threshold=82.0)
                self.assertIsNone(match)

    def test_noise_words_do_not_reduce_score(self):
        match, score = match_project(
            "1200 Main St Project",
            ["1200 Main Street Renovation"],
        )
        self.assertEqual(match, "1200 Main Street Renovation")
        self.assertEqual(score, 100.0)

    def test_critical_identifier_mismatches_are_hard_fails(self):
        cases = [
            ("1200 Main St Phase 1", "1200 Main Street Phase 2"),
            ("400 Oak Ave Tower B", "400 Oak Avenue Tower A"),
            ("75 Central Bldg 2", "75 Central Building 1"),
        ]
        for dirty_name, official_name in cases:
            with self.subTest(dirty_name=dirty_name):
                self.assertEqual(
                    match_project(dirty_name, [official_name]),
                    (None, 0.0),
                )

    def test_numeros_y_direcciones_asimetricas(self):
        resultado1, _ = match_project(
            "24-011 2460 Australian Ave",
            ["2460 Australian Ave", "100 Main St"],
        )
        self.assertEqual(resultado1, "2460 Australian Ave")

        resultado2, _ = match_project(
            "240 Main St",
            ["250 Main St", "100 Broadway"],
        )
        self.assertNotEqual(resultado2, "250 Main St")

        resultado3, _ = match_project(
            "North Tower South Campus",
            ["North Tower South Campus", "East Wing"],
        )
        self.assertEqual(resultado3, "North Tower South Campus")

        resultado4, _ = match_project(
            "South Campus",
            ["Campus", "North Wing"],
        )
        self.assertEqual(resultado4, "Campus")

    def test_default_threshold_rejects_low_score(self):
        match, score = match_project(
            "unrelated project name",
            ["1200 Main Street"],
        )
        self.assertIsNone(match)
        self.assertLess(score, 80.0)

    def test_ambiguous_candidates_are_rejected(self):
        match, score = match_project(
            "Main Street Lofts",
            ["Main Street Lofts", "Main St Lofts"],
        )
        self.assertIsNone(match)
        self.assertEqual(score, 100.0)

    def test_match_metrics_reflect_the_selected_candidate(self):
        match, _, metrics, candidates = match_project_with_metrics(
            "2460 North Australian",
            ["2460 N Australian Ave", "500 Broadway"],
        )
        self.assertEqual(match, "2460 N Australian Ave")
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics["word_overlap"], 75.0)
        self.assertEqual(metrics["identifier_compatibility"], 100.0)
        self.assertEqual(metrics["noise_retention"], 100.0)
        self.assertEqual(
            [candidate["name"] for candidate in candidates],
            ["2460 N Australian Ave", "500 Broadway"],
        )
        self.assertGreaterEqual(
            candidates[0]["confidence_score"],
            candidates[1]["confidence_score"],
        )


if __name__ == "__main__":
    unittest.main()