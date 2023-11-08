export interface Entities {
    styles: Style[],
    hops: Hop[],
    fermentables: Fermentable[],
    yeasts: Yeast[]
}

export interface Style {
    id: string
    name: string
    parent: string
}

export interface Ingredients {
    id: string
    name: string
}

export interface Hop extends Ingredients{}
export interface Fermentable extends Ingredients{}
export interface Yeast extends Ingredients{}

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
    {id: 'typical-styles-relative', title: 'Popularity within Beer Styles', category: 'Beer Styles', size: 'l'},
    {id: 'typical-styles-absolute', title: 'Common Beer Styles', category: 'Beer Styles', size: 'l'},
    {id: 'popular-styles', title: 'Popular Styles', category: 'Beer Styles', size: 'm'},
    {id: 'trending-styles', title: 'Trending Styles', category: 'Beer Styles', size: 'm'},

    // Hops
    {id: 'popular-hops', title: 'Most Used Hops', category: 'Hops', size: 'm'},
    {id: 'popular-hops-amount', title: 'Hop Dosage', category: 'Hops', size: 'l'},
    {id: 'hop-pairings', title: 'Hop Pairings', category: 'Hops', size: 'l'},
    {id: 'trending-hops', title: 'Trending Hops', category: 'Hops', size: 'm'},

    // Fermentables
    {id: 'popular-fermentables', title: 'Most Used Fermentables', category: 'Fermentables', size: 'm'},
    {id: 'popular-fermentables-amount', title: 'Amount of Fermentables', category: 'Fermentables', size: 'l'},

    // Yeasts
    {id: 'popular-yeasts', title: 'Most Used Yeasts', category: 'Yeasts', size: 'm'},
    {id: 'trending-yeasts', title: 'Trending Yeasts', category: 'Yeasts', size: 'm'},

    // Recipes
    {id: 'recipes', title: 'Brewing Recipes', category: 'Recipes', size: 's'},
]
