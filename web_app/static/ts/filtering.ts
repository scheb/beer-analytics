import {Slider, SliderChangeEventArgs} from "@syncfusion/ej2-inputs";
import {CheckBoxSelection, MultiSelect, MultiSelectChangeEventArgs} from "@syncfusion/ej2-dropdowns";
import {delay, intersect} from "./utils";
import {ABV_RANGE, IBU_RANGE, OG_RANGE, SRM_RANGE, STYLES} from "./data";

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
    private readonly _onChange: Function;
    private _selected: Array<string> = new Array<string>()

    constructor(allowedValues: Array<string>, onChange: Function) {
        this.allowedValues = allowedValues
        this._onChange = onChange;
    }

    get selected(): Array<string> {
        return this._selected;
    }

    public setSelection(values: Array<string>): void {
        const oldSelected = this.selected
        this._selected = intersect<string>(values, this.allowedValues)

        // Has it changed?
        if (oldSelected.length !== this.selected.length) {
            // Simple check, did the number of elements change?
            this._onChange()
        } else if (intersect(oldSelected, this._selected).length === this._selected.length) {
            // More complex check, did the elements change?
            this._onChange()
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
}

class FilterState  {
    public readonly style: MultiSelectValue
    public readonly ibu: MinMaxValue
    public readonly abv: MinMaxValue
    public readonly srm: MinMaxValue
    public readonly og: MinMaxValue

    constructor(onChange: Function) {
        this.style = new MultiSelectValue(STYLES.map((s) => s.id), onChange)
        this.ibu = new MinMaxValue(IBU_RANGE[0], IBU_RANGE[1], 1, onChange)
        this.abv = new MinMaxValue(ABV_RANGE[0], ABV_RANGE[1], 1, onChange)
        this.srm = new MinMaxValue(SRM_RANGE[0], SRM_RANGE[1], 1, onChange)
        this.og = new MinMaxValue(OG_RANGE[0], OG_RANGE[1], 2, onChange)
    }

    public loadState(queryValues: URLSearchParams): void {
        this.style.setFromQueryValue(queryValues.get('styles'))
        this.ibu.setFromQueryValue(queryValues.get('ibu'))
        this.abv.setFromQueryValue(queryValues.get('abv'))
        this.srm.setFromQueryValue(queryValues.get('srm'))
        this.og .setFromQueryValue(queryValues.get('og'))
    }

    public toQuery(queryValues: URLSearchParams): void {
        queryValues.set('styles', this.style.toQueryValue())
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

    constructor() {
        this.filters = new FilterState(this.onFiltersChange.bind(this))
        this.charts = new MultiSelectValue([], this.onChartsChange.bind(this))  // TODO allowed values
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
        this.stateChangeCallback()
        this.filtersChangeCallback()
    }

    private onChartsChange(): void {
        this.stateChangeCallback()
        this.chartsChangeCallback()
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
    private readonly mainContainer: HTMLElement
    private analyzerQuery: AnalyzerQuery
    private analyzerState: AnalyzerState
    private analyzerFilterUi: AnalyzerFilterUi
    private isInitialized: boolean = false
    private resultsContainer: HTMLElement
    private onInitialize: Function

    constructor(mainElement: HTMLElement, onInitialize: Function) {
        this.mainContainer = mainElement
        this.onInitialize = onInitialize

        this.analyzerQuery = new AnalyzerQuery()
        this.analyzerState = new AnalyzerState()

        const loadState = this.analyzerQuery.isAnalyzerPage()
        if (loadState) {
            this.analyzerState.loadState(this.analyzerQuery.getQuery())
        }

        this.analyzerFilterUi = new AnalyzerFilterUi(this.analyzerState)

        // Load the current state
        if (loadState) {
            this.loadAnalyzerResults()
        }

        // Register events
        this.analyzerState.listenStateChange(this.onStateChange.bind(this))

        // // When the state changes, update the query parameters
        // this.analyzerState.onChange(function () {
        //     this.analyzerQuery.setQuery(this.analyzerState)
        // })
        //
        // // When the filter options change, refresh the charts
        // this.analyzerState.filters.onChange(function () {
        //     this.refreshCharts()
        // })
        //
        // this.analyzerState.charts.onAdd(function () {
        //     this.addChart()
        // })
        //
        // this.analyzerState.charts.onRemove(function () {
        //     this.removeChart()
        // })
    }

    private initialize(): void {
        if (this.isInitialized) {
            return
        }

        this.isInitialized = true
        this.mainContainer.innerHTML = '<h1>Results</h1><div id="analyzerResults"></div>'
        this.resultsContainer = document.getElementById('analyzerResults')

        this.onInitialize()
    }

    private loadAnalyzerResults(): void {
        this.initialize()
        // TODO add graphs
    }

    // Update the query on state change
    private onStateChange() {
        console.log(this.analyzerState)
        const queryParams = new URLSearchParams()
        this.analyzerState.toQuery(queryParams)
        this.analyzerQuery.setQuery(queryParams)
    }

    // private refreshView(): void {
    //     this.initialize()
    //     // TODO when filter options changed
    // }
    //
    // private addChart(): void {
    //     // TODO when a graph was added
    // }
    //
    // private removeChart(): void {
    //     // TODO when a graph was removed
    // }
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
        history.pushState({}, 'Beer Analytics – The analytical beer recipe database', url)
    }
}

class AnalyzerFilterUi {
    private state: AnalyzerState

    private styleSelect: StyleSelectUi
    private ibuSlider: SliderUi
    private abvSlider: SliderUi
    private srmSlider: SliderUi
    private ogSlider: SliderUi

    constructor(state: AnalyzerState) {
        this.state = state
        this.styleSelect = new StyleSelectUi('styles', this.state.filters.style)
        this.ibuSlider = new SliderUi('ibu', this.state.filters.ibu)
        this.abvSlider = new SliderUi('abv', this.state.filters.abv)
        this.srmSlider = new SliderUi('srm', this.state.filters.srm)
        this.ogSlider = new SliderUi('og', this.state.filters.og)
    }
}

class SliderUi {
    private state: MinMaxValue

    constructor(sliderName: string, state: MinMaxValue) {
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
        })
        rangeSlider.appendTo(container)
        rangeSlider.addEventListener('change', delay(this.onChange.bind(this), 500))
    }

    private onChange(evt: SliderChangeEventArgs) {
        if (evt.value instanceof Array) {
            this.state.setMinMax(evt.value[0], evt.value[1])
        }
    }
}

class StyleSelectUi {
    private state: MultiSelectValue

    constructor(name: string, state: MultiSelectValue) {
        this.state = state

        const container: Element = document.querySelector('[data-select="'+name+'"]')
        if (!(container instanceof HTMLElement)) {
            return
        }

        MultiSelect.Inject(CheckBoxSelection)
        const select: MultiSelect = new MultiSelect({
            // @ts-ignore
            dataSource: STYLES,
            value: this.state.selected,
            fields: { groupBy: 'parent', text: 'name', value: 'id' },
            mode: 'CheckBox',
            placeholder: 'Filter beer styles',
            showDropDownIcon: true,
            filterBarPlaceholder: 'Search beer styles',
            enableGroupCheckBox: true,
        })
        select.appendTo(container);
        select.addEventListener('change', this.onChange.bind(this))
    }

    private onChange(evt: MultiSelectChangeEventArgs) {
        if (evt.value instanceof Array) {
            // @ts-ignore
            this.state.setSelection(evt.value)
        }
    }
}

