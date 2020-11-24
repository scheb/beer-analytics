interface Style {
    id: string
    name: string
    parent: string
}

export const STYLES: Style[] = [
    {id: "01A", name: "American Light Lager", parent: "Standard American Beer"},
    {id: "01B", name: "American Lager", parent: "Standard American Beer"},
    {id: "01C", name: "Cream Ale", parent: "Standard American Beer"},
    {id: "01D", name: "American Wheat Beer", parent: "Standard American Beer"},
    {id: "02A", name: "International Pale Lager", parent: "International Lager"},
    {id: "02B", name: "International Amber Lager", parent: "International Lager"},
    {id: "02C", name: "International Dark Lager", parent: "International Lager"},
    {id: "03A", name: "Czech Pale Lager", parent: "Czech Lager"},
    {id: "03B", name: "Czech Premium Pale Lager", parent: "Czech Lager"},
    {id: "03C", name: "Czech Amber Lager", parent: "Czech Lager"},
    {id: "03D", name: "Czech Dark Lager", parent: "Czech Lager"},
    {id: "04A", name: "Munich Helles", parent: "Munich Helles"},
    {id: "04B", name: "Festbier", parent: "Munich Helles"},
    {id: "04C", name: "Helles Bock", parent: "Munich Helles"},
    {id: "05A", name: "German Leichtbier", parent: "Pale Bitter European Beer"},
    {id: "05B", name: "Kölsch", parent: "Pale Bitter European Beer"},
    {id: "05C", name: "German Helles Exportbier", parent: "Pale Bitter European Beer"},
    {id: "05D", name: "German Pils", parent: "Pale Bitter European Beer"},
    {id: "06A", name: "Märzen", parent: "Amber Malty European Lager"},
    {id: "06B", name: "Rauchbier", parent: "Amber Malty European Lager"},
    {id: "06C", name: "Dunkles Bock", parent: "Amber Malty European Lager"},
    {id: "07A", name: "Vienna Lager", parent: "Amber Bitter European Beer"},
    {id: "07B", name: "Altbier", parent: "Amber Bitter European Beer"},
    {id: "07C", name: "Kellerbier", parent: "Amber Bitter European Beer"},
    {id: "08A", name: "Munich Dunkel", parent: "Dark European Lager"},
    {id: "08B", name: "Schwarzbier", parent: "Dark European Lager"},
    {id: "09A", name: "Doppelbock", parent: "Strong European Beer"},
    {id: "09B", name: "Eisbock", parent: "Strong European Beer"},
    {id: "09C", name: "Baltic Porter", parent: "Strong European Beer"},
    {id: "10A", name: "Weissbier", parent: "German Wheat Beer"},
    {id: "10B", name: "Dunkles Weissbier", parent: "German Wheat Beer"},
    {id: "10C", name: "Weizenbock", parent: "German Wheat Beer"},
    {id: "11A", name: "Ordinary Bitter", parent: "British Bitter"},
    {id: "11B", name: "Best Bitter", parent: "British Bitter"},
    {id: "11C", name: "Strong Bitter", parent: "British Bitter"},
    {id: "12A", name: "British Golden Ale", parent: "Pale Commonwealth Beer"},
    {id: "12B", name: "Australian Sparkling Ale", parent: "Pale Commonwealth Beer"},
    {id: "12C", name: "English IPA", parent: "Pale Commonwealth Beer"},
    {id: "13A", name: "Dark Mild", parent: "Brown British Beer"},
    {id: "13B", name: "British Brown Ale", parent: "Brown British Beer"},
    {id: "13C", name: "English Porter", parent: "Brown British Beer"},
    {id: "14A", name: "Scottish Light", parent: "Scottish Ale"},
    {id: "14B", name: "Scottish Heavy", parent: "Scottish Ale"},
    {id: "14C", name: "Scottish Export", parent: "Scottish Ale"},
    {id: "15A", name: "Irish Red Ale", parent: "Irish Beer"},
    {id: "15B", name: "Irish Stout", parent: "Irish Beer"},
    {id: "15C", name: "Irish Extra Stout", parent: "Irish Beer"},
    {id: "16A", name: "Sweet Stout", parent: "Dark British Beer"},
    {id: "16B", name: "Oatmeal Stout", parent: "Dark British Beer"},
    {id: "16C", name: "Tropical Stout", parent: "Dark British Beer"},
    {id: "16D", name: "Foreign Extra Stout", parent: "Dark British Beer"},
    {id: "17A", name: "British Strong Ale", parent: "Strong British Ale"},
    {id: "17B", name: "Old Ale", parent: "Strong British Ale"},
    {id: "17C", name: "Wee Heavy", parent: "Strong British Ale"},
    {id: "17D", name: "English Barleywine", parent: "Strong British Ale"},
    {id: "18A", name: "Blonde Ale", parent: "Pale American Ale"},
    {id: "18B", name: "American Pale Ale", parent: "Pale American Ale"},
    {id: "19A", name: "American Amber Ale", parent: "Amber and Brown American Beer"},
    {id: "19B", name: "California Common ", parent: "Amber and Brown American Beer"},
    {id: "19C", name: "American Brown Ale", parent: "Amber and Brown American Beer"},
    {id: "20A", name: "American Porter", parent: "American Porter and Stout"},
    {id: "20B", name: "American Stout", parent: "American Porter and Stout"},
    {id: "20C", name: "Imperial Stout", parent: "American Porter and Stout"},
    {id: "21A", name: "American IPA", parent: "IPA"},
    {id: "21B", name: "Specialty IPA", parent: "IPA"},
    {id: "21B1", name: "Belgian IPA", parent: "Specialty IPA"},
    {id: "21B2", name: "Black IPA", parent: "Specialty IPA"},
    {id: "21B3", name: "Brown IPA", parent: "Specialty IPA"},
    {id: "21B4", name: "Red IPA", parent: "Specialty IPA"},
    {id: "21B5", name: "Rye IPA", parent: "Specialty IPA"},
    {id: "21B6", name: "White IPA", parent: "Specialty IPA"},
    {id: "21B7", name: "New England IPA", parent: "Specialty IPA"},
    {id: "21B8", name: "West Coast IPA", parent: "Specialty IPA"},
    {id: "22A", name: "Double IPA", parent: "Strong American Ale"},
    {id: "22B", name: "American Strong Ale", parent: "Strong American Ale"},
    {id: "22C", name: "American Barleywine", parent: "Strong American Ale"},
    {id: "22D", name: "Wheatwine", parent: "Strong American Ale"},
    {id: "23A", name: "Berliner Weisse", parent: "European Sour Ale"},
    {id: "23B", name: "Flanders Red Ale", parent: "European Sour Ale"},
    {id: "23C", name: "Oud Bruin", parent: "European Sour Ale"},
    {id: "23D", name: "Lambic", parent: "European Sour Ale"},
    {id: "23E", name: "Gueuze ", parent: "European Sour Ale"},
    {id: "23F", name: "Fruit Lambic", parent: "European Sour Ale"},
    {id: "24A", name: "Witbier", parent: "Belgian Ale"},
    {id: "24B", name: "Belgian Pale Ale", parent: "Belgian Ale"},
    {id: "24C", name: "Bière de Garde", parent: "Belgian Ale"},
    {id: "25A", name: "Belgian Blond Ale", parent: "Strong Belgian Ale"},
    {id: "25B", name: "Saison", parent: "Strong Belgian Ale"},
    {id: "25C", name: "Belgian Golden Strong Ale", parent: "Strong Belgian Ale"},
    {id: "26A", name: "Trappist Single", parent: "Trappist Ale"},
    {id: "26B", name: "Belgian Dubbel", parent: "Trappist Ale"},
    {id: "26C", name: "Belgian Tripel", parent: "Trappist Ale"},
    {id: "26D", name: "Belgian Dark Strong Ale", parent: "Trappist Ale"},
    {id: "27A", name: "Gose", parent: "Historical Beer"},
    {id: "27B", name: "Kentucky Common", parent: "Historical Beer"},
    {id: "27C", name: "Lichtenhainer", parent: "Historical Beer"},
    {id: "27D", name: "London Brown Ale", parent: "Historical Beer"},
    {id: "27E", name: "Piwo Grodziskie", parent: "Historical Beer"},
    {id: "27F", name: "Pre-Prohibition Lager", parent: "Historical Beer"},
    {id: "27G", name: "Pre-Prohibition Porter", parent: "Historical Beer"},
    {id: "27H", name: "Roggenbier", parent: "Historical Beer"},
    {id: "27I", name: "Sahti", parent: "Historical Beer"},
    {id: "28A", name: "Brett Beer", parent: "American Wild Ale"},
    {id: "28B", name: "Mixed-Fermentation Sour Beer", parent: "American Wild Ale"},
    {id: "28C", name: "Wild Specialty Beer", parent: "American Wild Ale"},
    {id: "29A", name: "Fruit Beer", parent: "Fruit Beer Variants"},
    {id: "29B", name: "Fruit and Spice Beer", parent: "Fruit Beer Variants"},
    {id: "29C", name: "Specialty Fruit Beer", parent: "Fruit Beer Variants"},
    {id: "30A", name: "Spice, Herb or Vegetable Beer", parent: "Spiced Beer"},
    {id: "30B", name: "Autumn Seasonal Beer", parent: "Spiced Beer"},
    {id: "30C", name: "Winter Seasonal Beer", parent: "Spiced Beer"},
    {id: "31A", name: "Alternative Grain Beer", parent: "Alternative Fermentables Beer"},
    {id: "31B", name: "Alternative Sugar Beer", parent: "Alternative Fermentables Beer"},
    {id: "32A", name: "Classic Style Smoked Beer", parent: "Smoked Beer"},
    {id: "32B", name: "Specialty Smoked Beer", parent: "Smoked Beer"},
    {id: "33A", name: "Wood-Aged Beer", parent: "Wood Beer"},
    {id: "33B", name: "Specialty Wood-Aged Beer", parent: "Wood Beer"},
    {id: "34A", name: "Clone Beer", parent: "Specialty Beer"},
    {id: "34B", name: "Mixed-Style Beer", parent: "Specialty Beer"},
    {id: "34C", name: "Experimental Beer", parent: "Specialty Beer"},
]

// Update values in analyze.py when limits are changed
export const IBU_RANGE: number[] = [0, 301]
export const ABV_RANGE: number[] = [0, 21]
export const SRM_RANGE: number[] = [0, 101]
export const OG_RANGE: number[] = [1000, 1151]

export interface ChartDefinition {
    id: string
    title: string
    subtitle?: string
    category: string
    size: string
}

export const CHARTS: ChartDefinition[] = [
    // Styles
    {id: 'typical-styles-absolute', title: 'Styles Breakdown', subtitle: 'by Number of Recipes', category: 'Beer Styles', size: 'l'},
    {id: 'typical-styles-relative', title: 'Styles Breakdown', subtitle: 'by Percent of Recipes', category: 'Beer Styles', size: 'l'},
    {id: 'popular-styles', title: 'Popular Styles', category: 'Beer Styles', size: 'm'},
    {id: 'trending-styles', title: 'Trending Styles', category: 'Beer Styles', size: 'm'},

    // Fermentables
    {id: 'popular-fermentables', title: 'Most Used Fermentables', category: 'Fermentables', size: 'm'},
    {id: 'popular-fermentables-amount', title: 'Typical Amount of Fermentables', category: 'Fermentables', size: 'l'},

    // Hops
    {id: 'popular-hops', title: 'Most Used Hops', category: 'Hops', size: 'm'},
    {id: 'trending-hops', title: 'Trending Hops', category: 'Hops', size: 'm'},
    {id: 'popular-hops-amount', title: 'Typical Amount of Hops', category: 'Hops', size: 'l'},
    {id: 'hop-pairings', title: 'Common Hop Pairings', category: 'Hops', size: 'l'},

    // Yeasts
    {id: 'popular-yeasts', title: 'Most Used Yeasts', category: 'Yeasts', size: 'm'},
    {id: 'trending-yeasts', title: 'Trending Yeasts', category: 'Yeasts', size: 'm'},
]
