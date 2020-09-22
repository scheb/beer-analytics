function display_graph(container_id, chart_url, config = {}) {
    display_graph_with_navigation(container_id, null, chart_url, config)
}

function display_graph_with_navigation(container_id, navigation_id, chart_url, config = {}) {
    let container = document.getElementById(container_id)
    if (!container) {
        return
    }

    let chart = new ChartMount(container, chart_url, config)

    if (navigation_id) {
        let navigation_tab_list = document.querySelectorAll('#' + navigation_id + ' a[data-toggle="tab"]')
        navigation_tab_list.forEach(function (tab) {
            tab.addEventListener('shown.bs.tab', function (e) {
                let filter = e.target.dataset['filter']
                let query = {}
                if (filter) {
                    query['filter'] = filter
                }
                chart.load(query)
            })
        })
    }

    chart.load()
}

class ChartMount {
    constructor(container, chartUrl, chartConfig) {
        this.current_request = null
        this.container = container
        this.chartUrl = chartUrl
        let defaultConfig = {responsive: true, displayModeBar: true}
        this.chartConfig = {...defaultConfig, ...chartConfig}
    }

    load(query = {}) {
        if (null !== this.current_request) {
            this.current_request.abort()
        }

        this.container.innerHTML = '<div class="chart-loading"><span></span></div>'

        let query_string = this.serializeFilter(query)
        let url = this.chartUrl + (query_string ? '?'+query_string : '')

        let self = this
        let xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                self.current_request = null
                if (xhr.status === 204) {
                    self.container.innerHTML = '<p class="no-data"><span>No data</span></p>'
                } else if (xhr.status === 200) {
                    self.container.innerHTML = '';
                    let data = JSON.parse(xhr.responseText);
                    Plotly.newPlot(self.container.id, data.data, data.layout, self.chartConfig)
                } else {
                    self.container.innerHTML = '<p class="no-data"><span>Failed loading data</span></p>'
                }
            }
        }

        this.current_request = xhr
        xhr.send();
    }

    serializeFilter = function (obj) {
        let str = [];
        for (let p in obj) {
            if (obj.hasOwnProperty(p)) {
                str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
            }
        }
        return str.join("&");
    }
}
