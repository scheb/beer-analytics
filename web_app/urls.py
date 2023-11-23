from django.urls import path, register_converter

from . import views
from .views import fermentable, hop, misc, style, yeast, trend, analyze, admin
from .views.utils import FORMATS


class ChartFormat:
    regex = "|".join(FORMATS)

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)


register_converter(ChartFormat, "cformat")

urlpatterns = [
    path("", views.misc.home, name="home"),
    path("legal/", misc.legal, name="legal"),
    path("about/", misc.about, name="about"),
    path("updates/", misc.updates, name="updates"),
    path("sitemap.xml", misc.sitemap, name="sitemap"),

    path("analyze/", analyze.result, name="analyze"),
    path("analyze/count.json", analyze.count, name="analyze_count"),
    path("analyze/entities.json", analyze.get_entities, name="analyze_entities"),
    path("analyze/charts/<str:chart_type>.json", analyze.chart, name="analyze_chart"),
    path("analyze/recipes/random.inc", analyze.recipes, name="analyze_recipes"),

    path("styles/", style.overview, name="style_overview"),
    path("styles/<str:category_slug>/", style.category, name="style_category"),
    path("styles/<str:category_slug>/charts/<str:chart_type>.json", style.category_chart_data, name="style_category_chart_data"),
    path("styles/<str:category_slug>/charts/<str:chart_type>.<cformat:format>", style.category_chart_image, name="style_category_chart"),
    path("styles/<str:category_slug>/recipes/random.inc", style.category_recipes, name="style_category_recipes"),

    path("styles/<str:category_slug>/<str:slug>/", style.detail, name="style_detail"),
    path("styles/<str:category_slug>/<str:slug>/charts/<str:chart_type>.json", style.chart_data, name="style_chart_data"),
    path("styles/<str:category_slug>/<str:slug>/charts/<str:chart_type>.<cformat:format>", style.chart_image, name="style_chart"),
    path("styles/<str:category_slug>/<str:slug>/recipes/random.inc", style.recipes, name="style_recipes"),

    path("hops/", views.hop.overview, name="hop_overview"),
    path("hops/flavors/", views.hop.flavor_overview, name="hop_flavor_overview"),
    path("hops/flavors/<str:flavor_id>/", views.hop.flavor_detail, name="hop_flavor_detail"),
    path("hops/<str:category_id>/", hop.category_or_tag, name="hop_category"),
    path("hops/<str:category_id>/<str:slug>/", hop.detail, name="hop_detail"),
    path("hops/<str:category_id>/<str:slug>/charts/<str:chart_type>.json", hop.chart_data, name="hop_chart_data"),
    path("hops/<str:category_id>/<str:slug>/charts/<str:chart_type>.<cformat:format>", hop.chart_image, name="hop_chart"),
    path("hops/<str:category_id>/<str:slug>/recipes/random.inc", hop.recipes, name="hop_recipes"),

    path("fermentables/", fermentable.overview, name="fermentable_overview"),
    path("fermentables/<str:category_id>/", fermentable.category, name="fermentable_category"),
    path("fermentables/<str:category_id>/<str:slug>/", fermentable.detail, name="fermentable_detail"),
    path("fermentables/<str:category_id>/<str:slug>/charts/<str:chart_type>.json", fermentable.chart_data, name="fermentable_chart_data"),
    path("fermentables/<str:category_id>/<str:slug>/charts/<str:chart_type>.<cformat:format>", fermentable.chart_image, name="fermentable_chart"),
    path("fermentables/<str:category_id>/<str:slug>/recipes/random.inc", fermentable.recipes, name="fermentable_recipes"),

    path("yeasts/", yeast.overview, name="yeast_overview"),
    path("yeasts/<str:type_id>/", yeast.type_overview, name="yeast_type"),
    path("yeasts/<str:type_id>/<str:slug>/", yeast.detail, name="yeast_detail"),
    path("yeasts/<str:type_id>/<str:slug>/charts/<str:chart_type>.json", yeast.chart_data, name="yeast_chart_data"),
    path("yeasts/<str:type_id>/<str:slug>/charts/<str:chart_type>.<cformat:format>", yeast.chart_image, name="yeast_chart"),
    path("yeasts/<str:type_id>/<str:slug>/recipes/random.inc", yeast.recipes, name="yeast_recipes"),

    path("trends/", trend.start, name="trend_root"),
    path("trends/popular-hops/", trend.popular_hops, name="trend_popular_hops"),
    path("trends/<str:period>/", trend.overview, name="trend_overview"),
    path("trends/<str:period>/<str:chart_type>.json", trend.chart_data, name="trend_chart_data"),
    path("trends/<str:period>/<str:chart_type>.<cformat:format>", trend.chart_image, name="trend_chart"),

    path("admin/", admin.overview, name="admin_root"),
    path("admin/<str:chart_type>.<cformat:format>", admin.chart, name="admin_chart"),
    path("admin/hops/", admin.hops, name="admin_hops"),
    path("admin/hops/qa/", admin.hops_qa, name="admin_hops_qa"),
    path("admin/yeasts/", admin.yeasts, name="admin_yeasts"),
    path("admin/fermentables/", admin.fermentables, name="admin_fermentables"),
    path("admin/descriptions/", admin.descriptions, name="admin_descriptions"),
]
