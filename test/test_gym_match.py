import unittest

from mod_bot.gym import build_full_name_graph, autocomplete_from_tree, candidates_key, get_approx_name, load_gyms


class TestGymNameFinder(unittest.TestCase):

    def test_load_gym(self):
        self.assertEqual(len(load_gyms(1, "./test")), 11)

    def test_find_gym(self):
        gym = ("avenuedupre",
               "Avenue Du Président Kennedy RER Maison De Radio France",
               "116 Avenue du Président Kennedy, 75016 Paris",
               48.8533702,
               2.2653691)
        gym_list = {gym[1]: gym}

        # Can use full name
        full_gym = get_approx_name("Avenue Du Président Kennedy RER Maison De Radio France", gym_list)
        self.assertEqual(full_gym, [gym], "full name did not work")

        # Can use longer name without accents
        no_accent_gym = get_approx_name("Avenue Du President Kennedy RER Maison De Radio France", gym_list)
        self.assertEqual(no_accent_gym, [gym], "accent did matter after all")

        # Can ignore case
        no_case_gym = get_approx_name("avenue du PreSIDent KENNEDY rer Maison De Radio France", gym_list)
        self.assertEqual(no_case_gym, [gym], "accent did matter after all")

        # Can autocomplete
        auto_gym = get_approx_name("avenue du pre", gym_list)
        self.assertEqual(auto_gym, [gym])

        # Can use short name
        short_gym = get_approx_name("avenuedupre", gym_list)
        self.assertEqual(short_gym, [gym], "Short name did not work")

        # Can use hyphen in name
        gym = ("avenuedupre",
               "l'Avenue Du Président Kennedy RER Maison De Radio France",
               "116 Avenue du Président Kennedy, 75016 Paris",
               48.8533702,
               2.2653691)
        hyphen_gym = get_approx_name("lavenue", {gym[1]: gym})
        self.assertEqual(hyphen_gym, [gym])

        # Can write wrong name and still get it
        gym = ("avenuedupre",
               "l'Avenue Du Président Kennedy RER Maison De Radio France",
               "116 Avenue du Président Kennedy, 75016 Paris",
               48.8533702,
               2.2653691)
        wrong_gym = get_approx_name("lavenuadelpresidento", {gym[1]: gym})
        self.assertEqual(wrong_gym, [gym], "didn't resolve with the wrong name")

        # Get multiple result when the search is ambiguous
        gym1 = ("avenueduprea",
                "l'Avenue Du Préasident Kennedy RER Maison De Radio France",
                "116 Avenue du Président Kennedy, 75016 Paris",
                48.8533702,
                2.2653691)
        gym2 = ("avenueduprel",
                "l'Avenue Du Prélsident Kennedy RER Maison De Radio France",
                "116 Avenue du Président Kennedy, 75016 Paris",
                48.8533702,
                2.2653691)
        ambiguous_gyms = get_approx_name("avenuedupre", {gym1[1]: gym1, gym2[1]: gym2})
        self.assertEqual(set(ambiguous_gyms), {gym1, gym2}, "Couldn't get multiple results")

    def test_build_graph(self):
        gym = ("avenuedupre",
               "Av du",
               )
        gym2 = ("avenuedepre",
                "Av de",
                )
        gym_list = {"Av du": gym, "Av de": gym2}
        tree = build_full_name_graph(gym_list)
        expected = {
            'a': {
                candidates_key: ['av du', 'av de'],
                'v': {
                    candidates_key: ['av du', 'av de'],
                    ' ':
                        {
                            candidates_key: ['av du', 'av de'],
                            'd':
                                {
                                    candidates_key: ['av du', 'av de'],
                                    'e': {candidates_key: ['av de']},
                                    'u': {candidates_key: ['av du']}
                                },
                        },
                }
            }
        }
        self.assertEqual(tree, expected, "Build graph did not work")

    def test_use_full_graph(self):
        gym = ("avenuedupre",
               "Av dul",
               )
        gym2 = ("avenuedepre",
                "Av del",
                )
        gym_list = {"Av dul": gym, "Av del": gym2}
        tree = build_full_name_graph(gym_list)

        self.assertEqual(autocomplete_from_tree(tree, "av del"), [gym2[1].lower()])
        self.assertEqual(autocomplete_from_tree(tree, "av dua"), [gym[1].lower()])
        self.assertEqual(autocomplete_from_tree(tree, "av d"), ["av dul", "av del"])

    def test_do_not_match_eagerly(self):
        gym = ('an arena', 'an arena somewhere in the world')
        tree = build_full_name_graph({"an arena somewhere in the world": gym})

        self.assertEqual(autocomplete_from_tree(tree, 'anngdkjfghdfog'), [])

    def test_proper_match(self):
        gyms = load_gyms(1, "./test")

        result = get_approx_name("porte", gyms)
        self.assertEqual(len(result), 5)

        result = get_approx_name("stade", gyms)
        self.assertEqual(len(result), 3)

        result = get_approx_name("église", gyms)
        self.assertEqual(len(result), 3)


