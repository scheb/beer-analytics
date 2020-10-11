beer-analytics 🕵️🍺
===================

**Analyzing the composition of beer recipes and visualize results**, built with Django, Pandas and Plotly.

Live website: https://www.beer-analytics.com/

The goal is to expand the knowledge how different beer styles are typically brewed and potentially uncover trends in
craft/home brewing.

The project has two components:

1) a recipe database with reliable data (clean and normalized, reduce outliers and bad data)
2) a user interface to execute data analysis (filtering, slicing and dicing) and present results in a visually appealing
   way

Setup
-----

### Requirements

- Python 3.8
- pip
- virtualenv (ideally)
- yarn (JS package manager)

### Steps

- `yarn install`
- Initialize `virtualenv` and enable it
- Install Python dependencies: `pip -r requirements.txt`
- Configure the application (see below)
- Apply database migrations `python makemigrations` + `python manage.py migrate`
- Load initial data `python manage.py load_initial_data`

### Configuration

Provide a `.env` file in the `beer_analytics` folder. An example can be found in `beer_analytics/.env.example`.

Per default the application starts with "dev" settings. Use `DJANGO_SETTINGS_MODULE` to use different settings according
to the environment:

```
# Production settings
DJANGO_SETTINGS_MODULE=beer_analytics.settings_prod

# Dev settings
DJANGO_SETTINGS_MODULE=beer_analytics.settings_dev
```

Recipe data import
------------------

Please note that for legal reasons the project comes with no recipe data included.

After setting up the application, recipes can be imported via CLI in various formats. Each recipe must have a unique id
assigned, which can be an arbitrary string.

**[BeerXML](http://www.beerxml.com/)**:

```bash
python manage.py load_beerxml_recipe recipe.xml unique_id
```

**[MMUM format](https://www.maischemalzundmehr.de/):**

```bash
python manage.py load_mmum_recipe recipe.json unique_id
```

**[BeerSmith format](https://beersmithrecipes.com/):**

```bash
python manage.py load_beersmith_recipe recipe.bsmx unique_id
```

Data Mapping
------------

Once recipes are imported, they need to be mapped to their respective styles and ingredients. Run the following
commands to execute the mapping. Any unmapped recipes will be processed:

```
python manage.py map_styles
python manage.py map_hops
python manage.py map_fermentables
python manage.py map_yeasts
```

Pre-calculated metrics
----------------------

The application is pre-calculating asn persisting some metrics on style and ingredients. To update these metrics, run:

```
python manage.py calculate_metrics
```

Security
--------

For information about the security policy and know security issues, see [SECURITY.md](SECURITY.md).

Contributing
------------

Want to contribute to this project? See [CONTRIBUTING.md](CONTRIBUTING.md).

License
-------

This software is available under the [Beerware License](LICENSE).
