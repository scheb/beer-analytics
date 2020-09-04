beer-analytics 🍺
=================

Web application written in Django to **analyze beers recipes and visualize results**.

The goal is to expand the knowledge how different beer styles are typically brewed and potentially uncover trends in
craft/home brewing.

The project has two components:

1) a recipe database with reliable data (clean and normalized, reduce outliers and bad data)
2) a user interface to execute data analysis (filtering, slicing and dicing) and present results in a visually appealing
   way

Recipe data import
------------------

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

License
-------

This software is available under the [WTFPL License](LICENSE).