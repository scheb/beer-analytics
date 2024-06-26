beer-analytics 🕵️🍺
===================

**Analyzing the composition of beer recipes and visualize results in a human-friendly way.**

Check out the live website: https://www.beer-analytics.com/

<p align="center"><img alt="Logo" src="screenshot.png" width="480" height="283" /></p>

What is Beer Analytics?
-----------------------

*Beer Analytics* is a **database of beer brewing recipes**, built specifically for data analysis. It is made for beer
enthusiasts and (home)brewers to provide detailed insights into brewing recipes, even when they're not an expert in data
analysis. The goal is to expand the knowledge how certain types of beer are typically brewed, ultimately helping
(home)brewers to compose better recipes themselves, and potentially uncover some trends in craft/home brewing.

The project has two main components:

1) a recipe database with (hopefully) reliable data (clean and normalized, reduce outliers and bad data)
2) a user interface to execute data analysis (filtering, slicing and dicing) and to present results in a visually
   appealing way

Application Setup
-----------------

### Requirements

- Docker installed locally
- [yarn](https://yarnpkg.com/) (JavaScript package manager) installed locally

### Setup Steps

- Install yarn dependencies: `yarn install`
- Create a configuration file (see below)
- Build and start the Docker container `docker compose up`
- Jump into Docker container `docker exec -it beer_analytics_django bash`
- Load initial data (known styles and ingredients) via `python manage.py load_initial_data`

### Configuration

Provide a `.env` file in the main folder. An example can be found in `.env.example`.

Per default the application starts with "dev" settings, which is likely what you want. Use the `DJANGO_SETTINGS_MODULE`
environment variable to use different settings according to the environment:

```
# Dev settings
DJANGO_SETTINGS_MODULE=config.settings_dev

# Production settings
DJANGO_SETTINGS_MODULE=config.settings_prod
```

The Docker container uses dev settings.

### Development

To start the application for development run the Docker container

`docker compose up`

which starts a webserver at `localhost:8000`.

In a second terminal run

`yarn start`

to start the Webpack dev server to compile CSS and JS files.

Recipe data
-----------

For legal reasons the project does not come with any recipe data included. You have to retrieve and import recipe data 
from the sources you'd like to analyze.

ℹ️ It is planned to add a database with anonymized data samples at some point. Sorry for inconvenience.

### Data Import

Recipes can be imported via CLI in various formats. Each recipe must have a unique id assigned, which can be an
arbitrary string. The following recipe formats are supported with their respective commands:

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

### Data Mapping

Once recipes are imported, they need to be mapped to the list of known styles and ingredients. Run the following
commands to execute the mapping. Any unmapped recipes will be processed:

```
python manage.py map_styles
python manage.py map_hops
python manage.py map_fermentables
python manage.py map_yeasts
```

These commands can be repeated any time and will process any recipes, which haven't been mapped yet. Please note that,
depending on the amount if recipes, this step can take a while.

### Pre-calculate metrics

The application is pre-calculating and persisting some metrics for style and ingredients. To update these metrics, run:

```
python manage.py calculate_metrics
python manage.py calculate_hop_pairings
```

Security
--------
For information about the security policy and know security issues, see [SECURITY.md](SECURITY.md). 

License
-------
This software is available under the [GPLv3](LICENSE) license.

Contributing
------------
You're welcome to contribute new features, such as new analysis/chart types or bug fixes, by creating a Pull Request.

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

Acknowledgments
---------------

Thank you [@kasperg3](https://github.com/kasperg3) for sharing data from his awesome [hops database](https://github.com/kasperg3/HopDatabase).

Support Me
----------
I love to hear from people using my work, it's giving me the motivation to keep working on it.

If you want to let me know you're finding it useful, please consider giving it a star ⭐ on GitHub.

If you love my work and want to say thank you, you can help me out for a beer 🍻️
[via PayPal](https://paypal.me/ChristianScheb).
