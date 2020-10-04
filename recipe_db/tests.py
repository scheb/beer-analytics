from django.test import TestCase

from recipe_db.mapping import get_product_id_variants


class ProductIdTest(TestCase):
    def test_product_id_variants(self):
        variants = list(get_product_id_variants('A1B'))

        self.assertEquals(4, len(variants))
        self.assertTrue('A1B' in variants)
        self.assertTrue('A 1 B' in variants)
        self.assertTrue('A1 B' in variants)
        self.assertTrue('A 1B' in variants)

    def test_product_id_variants_with_separators(self):
        variants = list(get_product_id_variants('A.1-B'))

        self.assertEquals(4, len(variants))
        self.assertTrue('A1B' in variants)
        self.assertTrue('A 1 B' in variants)
        self.assertTrue('A1 B' in variants)
        self.assertTrue('A 1B' in variants)
