import {getRequest, RequestResult} from "./request"
// @ts-ignore
import * as Plotly from 'plotly.js/lib/index-cartesian'
import {InteractionElement} from "./interaction"

const NOT_ENOUGH_DATA_TEXT = "Not enough data"
const MAX_RETRIES = 2

export class ChartConfig {
    responsive: boolean
    displayModeBar: boolean
    modeBarButtonsToRemove: string[]
    noDataText: string

    constructor() {
        this.responsive = true
        this.displayModeBar = true
        this.modeBarButtonsToRemove = ['lasso2d', 'select2d']
        this.noDataText = 'Not enough data'
    }
}

interface PlotlyData {
    data: Plotly.Data[]
    layout: Partial<Plotly.Layout>
}

export class ChartContainer {
    constructor(container: Element) {
        if (!(container instanceof HTMLElement)) {
            return
        }
        if (undefined === container.dataset['chart']) {
            return
        }

        const chartConfig = new ChartConfig()
        if (undefined !== container.dataset['chartOptions']) {
            try {
                let options = JSON.parse(container.dataset['chartOptions'])
                if (undefined !== options.displayModeBar) {
                    chartConfig.displayModeBar = !!options.displayModeBar
                }
                if (undefined !== options.noDataText) {
                    chartConfig.noDataText = options.noDataText
                }
            } catch (e) {
                // JSON syntax error, ignore
                console.log(container.dataset['chartOptions'], e)
            }
        }

        const chart = new Chart(container, container.dataset['chart'], chartConfig)

        if (container.id !== undefined) {
            const navigationContainer = document.querySelector('[data-chart-navigation="'+container.id+'"]')
            if (null !== navigationContainer) {
                new ChartNavigation(navigationContainer, function (filter: string): void {
                    let query: any = {}
                    if ('' !== filter) {
                        query['filter'] = filter
                    }
                    chart.load(query)
                })
            }
        }

        chart.load()
    }
}

export class Chart {
    private readonly container: HTMLElement
    private readonly chartUrl: string
    private readonly chartConfig: ChartConfig
    private currentRequest: any
    private query: object;
    private retries: number = 0

    constructor(container: Element, chartUrl: string, chartConfig: ChartConfig) {
        if (!(container instanceof HTMLElement)) {
            return
        }

        this.container = container
        this.chartUrl = chartUrl
        this.chartConfig = chartConfig
        this.currentRequest = null
    }

    public load(query: object = {}) {
        if (null !== this.currentRequest) {
            this.currentRequest.abort()
        }

        this.displayLoading()
        this.query = query
        this.currentRequest = getRequest(this.chartUrl, query, this.handleResponse.bind(this))
    }

    private reload() {
        this.load(this.query)
    }

    private retry() {
        ++this.retries
        this.reload()
    }

    private displayLoading() {
        this.container.classList.add('chart-loading')
        this.container.innerHTML = `<span></span>`
    }

    private handleResponse(response: RequestResult) {
        this.currentRequest = null
        this.container.classList.remove('chart-loading')
        if (response.status === 204) {
            this.handleNoData()
        } else if (response.status === 200) {
            this.handleRenderChart(response)
        } else {
            this.handleFailedLoadingData()
        }
    }

    private handleRenderChart(response: RequestResult) {
        this.container.innerHTML = ''
        const data = response.json<PlotlyData>()
        Plotly.newPlot(this.container, data.data, data.layout, this.chartConfig)
    }

    private handleNoData() {
        renderNoData(this.container, this.chartConfig.noDataText)
    }

    private handleFailedLoadingData() {
        renderFailedLoadingData(this.container, this.retries < MAX_RETRIES ? this.retry.bind(this) : null)
    }
}

class ChartNavigation {
    private navigation: HTMLElement;

    constructor(navigationContainer: Element, onSelect: Function) {
        if (!(navigationContainer instanceof HTMLElement)) {
            return
        }

        this.navigation = navigationContainer
        this.navigation.classList.remove('d-none')
        this.initTabs(onSelect);

        // Update styling
        this.updateStyle()
        window.addEventListener("resize", this.updateStyle.bind(this))
    }

    private initTabs(onSelect: Function) {
        const navigationTabList = this.navigation.querySelectorAll('a[data-bs-toggle="tab"]')
        navigationTabList.forEach(function (tab) {
            tab.addEventListener('shown.bs.tab', function (e) {
                if (e.target instanceof HTMLElement) {
                    const filter = e.target.dataset['filter']
                    onSelect(filter)
                }
            })
        })
    }

    private updateStyle() {
        const navElement = this.navigation.querySelector('.nav')
        navElement.className = navElement.className
            .replace('nav-tabs card-header-tabs', '')
            .replace('nav-pills card-header-pills', '')

        // Decide if to show tabs for pills
        if (navElement.clientHeight > 50) {
            navElement.className += " nav-pills card-header-pills"
        } else {
            navElement.className += " nav-tabs card-header-tabs"
        }
    }
}

export class RecipesContainer {
    constructor(container: Element) {
        if (!(container instanceof HTMLElement)) {
            return
        }
        if (undefined === container.dataset['recipes']) {
            return
        }

        const recipesUrl = container.dataset['recipes']
        new Recipes(container, recipesUrl)
    }
}

export class Recipes {
    private readonly container: HTMLElement
    private readonly recipesUrl: string;
    private retries: number = 0

    constructor(container: HTMLElement, recipesUrl: string) {
        this.container = container
        this.recipesUrl = recipesUrl
        this.loadData()
    }

    private loadData() {
        this.displayLoading()
        getRequest(this.recipesUrl, {}, this.handleResponse.bind(this))
    }

    private retry() {
        ++this.retries
        this.loadData()
    }

    private displayLoading() {
        this.container.classList.add('chart-loading')
        this.container.innerHTML = `<span></span>`
    }

    private handleResponse(response: RequestResult) {
        this.container.classList.remove('chart-loading')
        if (response.status === 204) {
            this.handleNoData()
        } else if (response.status === 200) {
            this.handleRenderChart(response)
        } else {
            this.handleFailedLoadingData()
        }
    }

    private handleRenderChart(response: RequestResult) {
        this.container.style.height = null
        this.container.innerHTML = response.data
        const reloadButton = this.container.querySelector("[data-reload]")
        new InteractionElement(reloadButton)
        reloadButton.addEventListener("click", this.onReloadClicked.bind(this))
    }

    private onReloadClicked() {
        this.container.style.height = this.container.clientHeight+'px'
        this.loadData()
    }

    private handleNoData() {
        renderNoData(this.container, NOT_ENOUGH_DATA_TEXT)
    }

    private handleFailedLoadingData() {
        renderFailedLoadingData(this.container, this.retries < MAX_RETRIES ? this.retry.bind(this) : null)
    }
}


function renderNoData(container: HTMLElement, label: string) {
    container.classList.add('chart-no-data')
    container.innerHTML = `<p>${label}</p>`
}


function renderFailedLoadingData(container: HTMLElement, retryCallback: Function|null) {
    container.classList.add('chart-no-data')
    let html = `<p>Failed loading data. Sorry for inconvenience!</p>`
    if (retryCallback != null) {
        html += `<p class="mt-2"><button class="btn btn-sm bg-light" data-retry="true">Try again?</button></p>`
    }
    container.innerHTML = html
    container.querySelector("[data-retry]").addEventListener("click", () => {
        retryCallback()
    })
}
