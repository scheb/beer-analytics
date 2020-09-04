from django.core.validators import MaxValueValidator, BaseValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class GreaterThanValueValidator(BaseValidator):
    message = _('Ensure this value is greater than %(limit_value)s (it is %(show_value)s).')
    code = 'greater_min_value'

    def compare(self, a, b):
        return a <= b


# https://www.dummies.com/food-drink/drinks/beer/beer-style-guidelines-hierarchy/
class Style(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    sub_category = models.CharField(max_length=255)


class Malt(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)


# http://www.hopslist.com/hops/
class Hop(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=16)


class Yeast(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)


class Recipe(models.Model):
    # Identifiers
    uid = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=255, default=None, blank=True, null=True)
    created = models.DateField(default=None, blank=True, null=True)

    # Characteristics
    style = models.ForeignKey(Style, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    style_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    extract_efficiency_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    extract_plato = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    alc_percent = models.FloatField(default=None, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    ebc = models.IntegerField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    ibu = models.IntegerField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])

    # Mashing
    mash_water = models.IntegerField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    sparge_water = models.IntegerField(default=None, blank=True, null=True, validators=[MinValueValidator(0)])

    # Boiling
    boiling_time = models.IntegerField(default=None, blank=True, null=True, validators=[MinValueValidator(0)])
    cast_out_wort = models.IntegerField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])

    def __str__(self):
        return self.uid

    @classmethod
    def get_uid(cls, uid: str):
        return cls.objects.get(uid=uid)

    @classmethod
    def exists_uid(cls, uid) -> bool:
        try:
            cls.get_uid(uid)
            return True
        except cls.DoesNotExist:
            return False

    @classmethod
    def delete_uid(cls, uid: str) -> None:
        try:
            recipe = cls.get_uid(uid)
            recipe.delete()
        except cls.DoesNotExist:
            pass


class RecipeMalt(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.ForeignKey(Malt, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])


class RecipeHop(models.Model):
    MASH = 'mash'
    FIRST_WORT = 'first_wort'
    BOIL = 'boil'
    AROMA = 'aroma'
    DRY_HOP = 'dry_hop'

    USE_CHOICES = (
        (MASH, 'Mash'),
        (FIRST_WORT, 'First Wort'),
        (BOIL, 'Boil'),
        (AROMA, 'Aroma'),
        (DRY_HOP, 'Dry Hop'),
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.ForeignKey(Hop, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
    use = models.CharField(max_length=16, default=None, blank=True, null=True, choices=USE_CHOICES)
    alpha = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0)])
    amount_percent = models.FloatField(default=None, blank=True, null=True, validators=[GreaterThanValueValidator(0), MaxValueValidator(100)])
    time = models.IntegerField(default=None, blank=True, null=True, validators=[MinValueValidator(0)])


class RecipeYeast(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    kind = models.CharField(max_length=255, default=None, blank=True, null=True)
    kind_raw = models.CharField(max_length=255, default=None, blank=True, null=True)
