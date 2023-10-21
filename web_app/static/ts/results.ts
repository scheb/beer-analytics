import {getRequest, RequestResult} from "./request"
// @ts-ignore
import * as Plotly from 'plotly.js/lib/index-cartesian'

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

interface RecipeData {
    name?: string
    author?: string
    url: string
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
        this.currentRequest = getRequest(this.chartUrl, query, this.handleResponse.bind(this))
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
        this.container.classList.add('chart-no-data')
        this.container.innerHTML = `<p>${this.chartConfig.noDataText}</p>`
    }

    private handleFailedLoadingData() {
        this.container.classList.add('chart-no-data')
        this.container.innerHTML = `<p>Failed loading data</p>`
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

export class Recipes {
    private readonly container: HTMLElement

    constructor(container: Element) {
        if (!(container instanceof HTMLElement)) {
            return
        }
        if (undefined === container.dataset['recipes']) {
            return
        }

        this.container = container
        const recipesUrl = this.container.dataset['recipes']
        getRequest(recipesUrl, {}, this.handleResponse.bind(this))
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
        this.container.innerHTML = ''
        const data = response.json<Array<RecipeData>>()
        let lis: HTMLElement[] = []
        data.forEach(function (item: RecipeData) {
            const title = document.createTextNode(null !== item.name ? item.name : 'Unknown')
            const li = document.createElement('li')
            const a = document.createElement('a')
            a.appendChild(title)
            a.href = item.url
            li.appendChild(a)
            if (null !== item.author) {
                li.append(document.createTextNode(' by '+item.author))
            }
            lis.push(li)
        });

        const ul = document.createElement('ul')
        ul.classList.add('column-list-wide')
        ul.append(...lis)
        this.container.append(ul)
    }

    private handleNoData() {
        this.container.classList.add('chart-no-data')
        this.container.innerHTML = `<p>Not enough data</p>`
    }

    private handleFailedLoadingData() {
        this.container.classList.add('chart-no-data')
        this.container.innerHTML = `<p>Failed loading data</p>`
    }
}
