import {Slider, SliderChangeEventArgs, SliderTooltipEventArgs} from "@syncfusion/ej2-inputs";
import {
    CheckBoxSelection,
    FilteringEventArgs,
    MultiSelect,
    MultiSelectChangeEventArgs
} from "@syncfusion/ej2-dropdowns";
import {DataManager, UrlAdaptor, Query} from '@syncfusion/ej2-data';
import {delay, groupBy, intersect, queryParamsToObject} from "./utils";
import {
    ABV_RANGE,
    ChartDefinition,
    Entities,
    CHARTS,
    IBU_RANGE,
    OG_RANGE,
    SRM_RANGE,
    Style,
    Hop,
    Ingredients
} from "./data";
import {getRequest, RequestResult} from "./request";
import {Chart, ChartConfig} from "./results";

class MinMaxValue {
    public readonly minLimit: number
    public readonly maxLimit: number
    public readonly step: number
    private readonly _onChange: Function

    private _minValue: number
    private _maxValue: number

    constructor(minLimit: number, maxLimit: number, step: number, onChange: Function) {
        this.minLimit = minLimit
        this.maxLimit = maxLimit
        this.step = step
        this._onChange = onChange

        // Init with min and max values
        this._minValue = this.minLimit
        this._maxValue = this.maxLimit
    }

    get minValue(): number {
        return this._minValue;
    }

    get maxValue(): number {
        return this._maxValue;
    }

    public setMinMax(minValue: number, maxValue: number): void {
        const oldMin = this.minValue
        const oldMax = this.maxValue
        this._minValue = Math.max(this.minLimit, minValue)
        this._maxValue = Math.min(this.maxLimit, maxValue)

        // Has it changed?
        if (oldMin !== this._minValue || oldMax !== this._maxValue) {
            this._onChange()
        }
    }

    public setFromQueryValue(queryValue?: string): void {
        if (null !== queryValue) {
            const parts = queryValue.split(',')
            if (parts.length == 2) {
                const minValue: number = +parts[0]
                const maxValue: number = +parts[1]
                if (!isNaN(minValue) && !isNaN(maxValue)) {
                    this.setMinMax(minValue, maxValue)
                    return
                }
            }
        }

        this.setMinMax(this.minLimit, this.maxLimit)
    }

    public toQueryValue(): string {
        return this._minValue + ',' + this._maxValue
    }
}

class MultiSelectValue {
    public readonly allowedValues: Array<string>
    private readonly onChange: Function;
    private _selected: Array<string> = new Array<string>()

    constructor(allowedValues: Array<string>, onChange: Function) {
        this.allowedValues = allowedValues
        this.onChange = onChange;
    }

    get selected(): Array<string> {
        return this._selected;
    }

    public isSelected(value: string): boolean {
        return this._selected.indexOf(value) !== -1
    }

    public setSelection(values: Array<string>): void {
        const oldSelected = this._selected
        this._selected = intersect<string>(values, this.allowedValues)
        this._selected = Array.from(new Set(this._selected))  // Unique list

        // Has it changed?
        if (oldSelected.length !== this._selected.length) {
            // Simple check, did the number of elements change?
            this.onChange()
        } else if (intersect(oldSelected, this._selected).length === this._selected.length) {
            // More complex check, did the elements change?
            this.onChange()
        }
    }

    public setFromQueryValue(queryValue?: string): void {
        if (null !== queryValue) {
            this.setSelection(queryValue.split(','))
        } else {
            this.setSelection([])
        }
    }

    public toQueryValue(): string {
        return this._selected.join(',')
    }

    public add(value: string): void {
        if (this.isSelected(value)) {
            return  // Already in list
        }

        this._selected.push(value)
        this.onChange()
    }

    public remove(value: string): void {
        const index = this._selected.indexOf(value, 0)
        if (index === -1) {
            return  // Not in list
        }

        this._selected.splice(index, 1)
        this.onChange()
    }
}

class FilterState  {
    public readonly style: MultiSelectValue
    public readonly hop: MultiSelectValue
    public readonly fermentable: MultiSelectValue
    public readonly yeast: MultiSelectValue
    public readonly ibu: MinMaxValue
    public readonly abv: MinMaxValue
    public readonly srm: MinMaxValue
    public readonly og: MinMaxValue

    constructor(onChange: Function, entities: Entities) {
        this.style = new MultiSelectValue(entities.styles.map((s) => s.id), onChange)
        this.hop = new MultiSelectValue(entities.hops.map((h) => h.id), onChange)
        this.fermentable = new MultiSelectValue(entities.fermentables.map((f) => f.id), onChange)
        this.yeast = new MultiSelectValue(entities.yeasts.map((y) => y.id), onChange)
        this.ibu = new MinMaxValue(IBU_RANGE[0], IBU_RANGE[1], 1, onChange)
        this.abv = new MinMaxValue(ABV_RANGE[0], ABV_RANGE[1], 1, onChange)
        this.srm = new MinMaxValue(SRM_RANGE[0], SRM_RANGE[1], 1, onChange)
        this.og = new MinMaxValue(OG_RANGE[0], OG_RANGE[1], 2, onChange)
    }

    public loadState(queryValues: URLSearchParams): void {
        this.style.setFromQueryValue(queryValues.get('styles'))
        this.hop.setFromQueryValue(queryValues.get('hops'))
        this.fermentable.setFromQueryValue(queryValues.get('fermentables'))
        this.yeast.setFromQueryValue(queryValues.get('yeasts'))
        this.ibu.setFromQueryValue(queryValues.get('ibu'))
        this.abv.setFromQueryValue(queryValues.get('abv'))
        this.srm.setFromQueryValue(queryValues.get('srm'))
        this.og .setFromQueryValue(queryValues.get('og'))
    }

    public toQuery(queryValues: URLSearchParams): void {
        queryValues.set('styles', this.style.toQueryValue())
        queryValues.set('hops', this.hop.toQueryValue())
        queryValues.set('fermentables', this.fermentable.toQueryValue())
        queryValues.set('yeasts', this.yeast.toQueryValue())
        queryValues.set('ibu', this.ibu.toQueryValue())
        queryValues.set('abv', this.abv.toQueryValue())
        queryValues.set('srm', this.srm.toQueryValue())
        queryValues.set('og', this.og.toQueryValue())
    }
}

class AnalyzerState {
    public readonly filters: FilterState
    public readonly charts: MultiSelectValue

    private stateChangeCallback: Function = function() {}
    private filtersChangeCallback: Function = function() {}
    private chartsChangeCallback: Function = function() {}

    constructor(entities: Entities) {
        this.filters = new FilterState(this.onFiltersChange.bind(this), entities)
        this.charts = new MultiSelectValue(CHARTS.map((chart) => chart.id), this.onChartsChange.bind(this))
    }

    public loadState(queryValues: URLSearchParams) {
        this.filters.loadState(queryValues)
        this.charts.setFromQueryValue(queryValues.get('charts'))
    }

    public toQuery(queryValues: URLSearchParams): void {
        this.filters.toQuery(queryValues)
        queryValues.set('charts', this.charts.toQueryValue())
    }

    private onFiltersChange(): void {
        this.filtersChangeCallback()
        this.stateChangeCallback()
    }

    private onChartsChange(): void {
        this.chartsChangeCallback()
        this.stateChangeCallback()
    }

    public listenStateChange(callback: Function): void {
        this.stateChangeCallback = callback
    }

    public listenFiltersChange(callback: Function): void {
        this.filtersChangeCallback = callback
    }

    public listenChartsChange(callback: Function): void {
        this.chartsChangeCallback = callback
    }
}

export class Analyzer {
    private readonly analyzerQuery: AnalyzerQuery
    private analyzerState: AnalyzerState
    private analyzerFilterUi: AnalyzerFilterUi
    private readonly onInitialize: Function
    private resultUi?: ResultUi = null
    private entities: Entities;

    constructor(onInitialize: Function) {
        this.onInitialize = onInitialize
        this.analyzerQuery = new AnalyzerQuery()
        getRequest("/analyze/entities.json", {}, this.handleEntitiesResponse.bind(this))
    }

    private handleEntitiesResponse(response: RequestResult) {
        if (response.status !== 200) {
            return
        }

        this.entities = response.json<Entities>();
        this.analyzerState = new AnalyzerState(this.entities)

        const loadState = this.analyzerQuery.isAnalyzerPage()
        if (loadState) {
            this.analyzerState.loadState(this.analyzerQuery.getQuery())
        }

        this.analyzerFilterUi = new AnalyzerFilterUi(this.analyzerState, this.entities)

        // Load the current state
        if (loadState) {
            this.ensureInitialized()
        }

        // Register events
        this.analyzerState.listenStateChange(this.onStateChange.bind(this))
    }

    private ensureInitialized(): void {
        if (null !== this.resultUi) {
            return
        }

        this.resultUi = new ResultUi(this.analyzerState)
        this.onInitialize()
    }

    // Update the query on state change
    private onStateChange(): void {
        const queryParams = new URLSearchParams()
        this.analyzerState.toQuery(queryParams)
        this.analyzerQuery.setQuery(queryParams)
        this.ensureInitialized()
    }
}

class AnalyzerQuery {
    public isAnalyzerPage(): boolean {
        return window.location.pathname.startsWith('/analyze/')
    }

    public getQuery(): URLSearchParams {
        if (!window.location.search) {
            return new URLSearchParams()
        }
        return new URLSearchParams(window.location.search)
    }

    public setQuery(queryParams: URLSearchParams): void {
        let url = '/analyze/'
        let queryString: string
        if (null !== (queryString = queryParams.toString())) {
            url += '?'+queryString
        }
        history.pushState({}, 'Custom Analysis | Beer-Analytics', url)
        document.querySelector('title').text = 'Custom Analysis | Beer-Analytics'
    }
}

class AnalyzerFilterUi {
    private state: AnalyzerState

    private styleSelect: StyleSelectUi
    private hopSelect: IngredientSelectUi
    private fermentableSelect: IngredientSelectUi
    private yeastSelect: IngredientSelectUi
    private ibuSlider: SliderUi
    private abvSlider: SliderUi
    private srmSlider: SliderUi
    private ogSlider: SliderUi

    constructor(state: AnalyzerState, entities: Entities) {
        this.state = state
        this.styleSelect = new StyleSelectUi('styles', this.state.filters.style, entities.styles)
        this.hopSelect = new IngredientSelectUi('hops', this.state.filters.hop, 'hops', entities.hops)
        this.fermentableSelect = new IngredientSelectUi('fermentables', this.state.filters.fermentable, 'fermentables', entities.fermentables)
        this.yeastSelect = new IngredientSelectUi('yeasts', this.state.filters.yeast, 'yeasts', entities.yeasts)
        this.ibuSlider = new SliderUi('ibu', this.state.filters.ibu)
        this.abvSlider = new SliderUi('abv', this.state.filters.abv)
        this.srmSlider = new SliderUi('srm', this.state.filters.srm)
        this.ogSlider = new SliderUi('og', this.state.filters.og, 0.001)
    }
}

class SliderUi {
    private state: MinMaxValue

    constructor(sliderName: string, state: MinMaxValue, factor: number = 1) {
        this.state = state

        const container: Element = document.querySelector('[data-range-slider="'+sliderName+'"]')
        if (!(container instanceof HTMLElement)) {
            return
        }

        // Create the slider
        const rangeSlider: Slider = new Slider({
            type: 'Range',
            min: this.state.minLimit,
            max: this.state.maxLimit,
            step: this.state.step,
            value: [this.state.minValue, this.state.maxValue],
            tooltip: { isVisible: true, placement: 'Before', showOn: 'Auto' },
            tooltipChange: function (args: SliderTooltipEventArgs): void {
                if (args.value instanceof Array && args.value.length === 2) {
                    args.text = ""+this.formatNumber(args.value[0], factor)+" – "+this.formatNumber(args.value[1], factor)
                }
            }.bind(this),
        })
        rangeSlider.appendTo(container)
        rangeSlider.addEventListener('change', delay(this.onChange.bind(this), 500))
    }

    private formatNumber(value: number, factor: number): string {
        if (value <= this.state.minLimit) {
            return 'Min'
        }
        if (value >= this.state.maxLimit) {
            return 'Max'
        }
        return (new Intl.NumberFormat('en-US')).format(value*factor)
    }

    private onChange(evt: SliderChangeEventArgs) {
        if (evt.value instanceof Array) {
            this.state.setMinMax(evt.value[0], evt.value[1])
        } else {
            console.log("ignored change event", evt)
        }
    }
}

class StyleSelectUi {
    private state: MultiSelectValue

    constructor(name: string, state: MultiSelectValue, styles: Style[]) {
        this.state = state

        const container: Element = document.querySelector('[data-select="'+name+'"]')
        if (!(container instanceof HTMLElement)) {
            return
        }

        MultiSelect.Inject(CheckBoxSelection)
        const select: MultiSelect = new MultiSelect({
            // @ts-ignore
            dataSource: styles,
            value: this.state.selected,
            fields: { groupBy: 'parent', text: 'name', value: 'id' },
            mode: 'CheckBox',
            placeholder: 'Filter beer styles',
            showDropDownIcon: true,
            filterBarPlaceholder: 'Search beer styles',
            enableGroupCheckBox: true,
            filtering: function (e: FilteringEventArgs): void {
                let query = new Query()
                query = (e.text != "") ? query.where("name", "contains", e.text, true) : query
                //pass the filter data source, filter query to updateData method.
                // @ts-ignore
                e.updateData(styles, query)
            },
        })
        select.appendTo(container)
        select.addEventListener('change', this.onChange.bind(this))
    }

    private onChange(evt: MultiSelectChangeEventArgs) {
        if (evt.value instanceof Array) {
            // @ts-ignore
            this.state.setSelection(evt.value)
        }
    }
}


class IngredientSelectUi {
    private state: MultiSelectValue

    constructor(name: string, state: MultiSelectValue, ingredientName: string, ingredients: Ingredients[]) {
        this.state = state

        const container: Element = document.querySelector('[data-select="'+name+'"]')
        if (!(container instanceof HTMLElement)) {
            return
        }

        const select: MultiSelect = new MultiSelect({
            // @ts-ignore
            dataSource: ingredients,
            value: this.state.selected,
            fields: { text: 'name', value: 'id' },
            placeholder: 'Filter ' + ingredientName,
            allowFiltering: true,
            filterBarPlaceholder: 'Search ' + ingredientName,
            filtering: function (e: FilteringEventArgs): void {
                let query = new Query()
                query = (e.text != "") ? query.where("name", "contains", e.text, true) : query
                //pass the filter data source, filter query to updateData method.
                // @ts-ignore
                e.updateData(ingredients, query)
            },
        });
        select.appendTo(container)
        select.addEventListener('change', this.onChange.bind(this))
    }

    private onChange(evt: MultiSelectChangeEventArgs) {
        if (evt.value instanceof Array) {
            // @ts-ignore
            this.state.setSelection(evt.value)
        }
    }
}

class ResultUi {
    private analyzerState: AnalyzerState
    private recipeCountUi: RecipeCountUi
    private chartUis: Array<ChartUi> = new Array<ChartUi>()
    private resultsContainer: HTMLElement

    constructor(analyzerState: AnalyzerState) {
        this.analyzerState = analyzerState
        this.initializeUi()
        this.analyzerState.listenFiltersChange(this.onFiltersChange.bind(this))
    }

    private initializeUi(): void {
        const mainContainer = document.querySelector('main')

        // Render results UI scaffold
        mainContainer.innerHTML = `
            <div class="analyzer-results">
                <p class="analyzer-count">Found <strong id="analyzerRecipesCount"></strong> matching recipes.</p>
                <div id="analyzerCharts"></div>
                <div id="analyzerAddButton" class="add-chart-btn">
                    <p class="head">Select the data analysis you're interested in</p>
                    <div id="analyzerChartSelect" class="add-chart-list"></div>
                </div>
            </div>
        `
        const recipesCountContainer = document.getElementById('analyzerRecipesCount')
        this.resultsContainer = document.getElementById('analyzerCharts')

        // Render in available charts
        const chartSelect = document.getElementById('analyzerChartSelect')
        const chartGroups = groupBy(CHARTS, c => c.category)
        let chartsList = ''
        for (let chartGroup in chartGroups) {
            let chartGroupHtml = ''
            for (let chart of chartGroups[chartGroup]) {
                let subtitle = ''
                if (null !== chart.subtitle && undefined !== chart.subtitle) {
                    subtitle = chart.subtitle
                }
                chartGroupHtml += `<li><button class="btn btn-secondary px-2 py-1" data-chart-type="${chart.id}">${chart.title} ${subtitle}</button></li>`
            }
            chartsList += `<div class="add-chart-group"><strong>${chartGroup}</strong><ul class="list-unstyled">${chartGroupHtml}</ul></div>`
        }
        chartSelect.innerHTML = chartsList
        this.updateChartListState()
        document.querySelectorAll('#analyzerAddButton button').forEach((button: HTMLElement) => {
            button.addEventListener('click', this.onClickAddButton.bind(this))
        })

        // Display number of recipes
        this.recipeCountUi = new RecipeCountUi(recipesCountContainer, this.analyzerState)

        // Initialize selected charts
        this.analyzerState.charts.selected.forEach((chartType: string) => {
            this.createChart(chartType)
        })
    }

    private createChart(chartType: string) {
        const chartUi = new ChartUi(this.resultsContainer, this.analyzerState, chartType, () => {
            this.onChartRemoved(chartType)
        })
        this.chartUis.push(chartUi)
        this.analyzerState.charts.add(chartType)
    }

    private updateChartListState(): void {
        document.querySelectorAll('#analyzerChartSelect button').forEach((button: HTMLButtonElement) => {
            const chartType = button.dataset['chartType']
            button.disabled = this.analyzerState.charts.isSelected(chartType)
        })
    }

    private onChartRemoved(chartType: string) {
        // When a chart is remove, remove it from the state and refresh button
        this.analyzerState.charts.remove(chartType)
        this.updateChartListState()

        // Remove ChartUi
        for (let index = 0; index < this.chartUis.length; index++) {
            let chartUi = this.chartUis[index]
            if (chartUi.chartType === chartType) {
                this.chartUis.splice(index, 1)
                break
            }
        }
    }

    private onFiltersChange(): void {
        // Refresh recipe count and charts
        this.recipeCountUi.refresh()
        this.chartUis.forEach((chartUi: ChartUi) => chartUi.refresh())
    }

    private onClickAddButton(evt: Event): void {
        if (evt.target instanceof HTMLElement && undefined !== evt.target.dataset['chartType']) {
            const chartType = evt.target.dataset['chartType']
            if (!this.analyzerState.charts.isSelected(chartType)) {
                this.createChart(chartType)
                this.updateChartListState()
            }
        }
    }
}

class ChartUi {
    private readonly element: HTMLElement
    private readonly analyzerState: AnalyzerState
    public readonly chartType: string
    public readonly chartDefinition: ChartDefinition
    private readonly onRemove: Function
    private readonly chart: Chart

    constructor(container: HTMLElement, analyzerState: AnalyzerState, chartType: string, onRemove: Function) {
        this.chartType = chartType
        this.chartDefinition = this.getChartDefinition(chartType)
        this.analyzerState = analyzerState
        this.onRemove = onRemove

        this.element = document.createElement('div')
        this.element.id = 'chart-element-'+this.chartType
        const anchor = 'chart-'+this.chartType
        const chartUrl = '/analyze/charts/'+this.chartType+'.json'
        let subtitle = ''
        console.log(this.chartDefinition.subtitle)
        if (null !== this.chartDefinition.subtitle && undefined !== this.chartDefinition.subtitle) {
            subtitle = `<small class="text-muted">${this.chartDefinition.subtitle}</small>`
        }
        this.element.innerHTML = `
            <section class="card card-chart">
                <div class="card-header">
                    <button type="button" class="btn-close mt-2 float-end" aria-label="Close"></button>
                    <h2><a href="#${anchor}" id="${anchor}" class="anchor"><span></span></a>${this.chartDefinition.title} ${subtitle}</h2>
                </div>
                <div class="card-body">
                    <div class="chart-container chart-${this.chartDefinition.size}"></div>
                </div>
            </section>
        `
        this.element.querySelector('button.btn-close').addEventListener('click', this.onClickCloseButton.bind(this))

        // Add to results container
        container.appendChild(this.element)

        // Init Plotly
        const plotlyContainer = this.element.querySelector('.chart-container')
        this.chart = new Chart(plotlyContainer, chartUrl, new ChartConfig())

        // Display recipes count based on current filter state
        this.refresh()
    }

    public refresh(): void {
        const queryParams = new URLSearchParams()
        this.analyzerState.filters.toQuery(queryParams)
        this.chart.load(queryParamsToObject(queryParams.entries()))
    }

    public onClickCloseButton(): void {
        this.element.remove()
        this.onRemove()
    }

    private getChartDefinition(chartType: string): ChartDefinition {
        for (let chart of CHARTS) {
            if (chart.id === chartType) {
                return chart
            }
        }
    }
}

class RecipeCountUi {
    private container: HTMLElement
    private analyzerState: AnalyzerState

    constructor(container: HTMLElement, analyzerState: AnalyzerState) {
        this.container = container
        this.analyzerState = analyzerState;

        // Display recipes count based on current filter state
        this.refresh()
    }

    public refresh(): void {
        this.container.innerHTML = ''
        this.container.classList.add('loading')

        const requestUrl = '/analyze/count.json'
        const queryParams = new URLSearchParams()
        this.analyzerState.toQuery(queryParams)
        getRequest(requestUrl, queryParamsToObject(queryParams.entries()), this.handleResponse.bind(this))
    }

    private handleResponse(response: RequestResult) {
        this.container.classList.remove('chart-loading')
        if (response.status === 200) {
            this.handleRenderCount(response)
        } else {
            this.handleFailedLoadingData()
        }
    }

    private handleRenderCount(response: RequestResult) {
        this.container.classList.remove('loading')
        const data = response.json<CountData>()
        this.container.innerHTML = (new Intl.NumberFormat('en-US')).format(data.count)
    }

    private handleFailedLoadingData() {
        this.container.classList.remove('loading')
        this.container.innerHTML = '?'
    }
}

interface CountData {
    count: number
}
