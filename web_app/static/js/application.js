function display_graph(container_id, chart_url, config) {
    config = (typeof config !== 'undefined') ?  config : {}
    display_graph_with_navigation(container_id, null, chart_url, config)
}

function display_graph_with_navigation(container_id, navigation_id, chart_url, config) {
    config = (typeof config !== 'undefined') ?  config : {}
    var container = document.getElementById(container_id)
    if (!container) {
        return
    }

    var chart = new ChartMount(container, chart_url, config)

    if (navigation_id) {
        var navigation_tab_list = document.querySelectorAll('#' + navigation_id + ' a[data-toggle="tab"]')
        navigation_tab_list.forEach(function (tab) {
            tab.addEventListener('shown.bs.tab', function (e) {
                var filter = e.target.dataset['filter']
                var query = {}
                if (filter) {
                    query['filter'] = filter
                }
                chart.load(query)
            })
        })
    }

    chart.load()
}

function ChartMount(container, chartUrl, chartConfig) {
    this.current_request = null
    this.container = container
    this.chartUrl = chartUrl

    // Config defaults
    this.chartConfig = chartConfig
    this.chartConfig.responsive = this.chartConfig.responsive === undefined ? true : this.chartConfig.responsive
    this.chartConfig.displayModeBar = this.chartConfig.displayModeBar === undefined ? true : this.chartConfig.displayModeBar
}

ChartMount.prototype.load = function(query) {
    query = (typeof query !== 'undefined') ?  query : {}
    if (null !== this.current_request) {
        this.current_request.abort()
    }

    this.container.innerHTML = '<div class="chart-loading"><span></span></div>'

    var query_string = this.serializeFilter(query)
    var url = this.chartUrl + (query_string ? '?'+query_string : '')

    var self = this
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            self.current_request = null
            if (xhr.status === 204) {
                self.container.innerHTML = '<p class="no-data"><span>No data</span></p>'
            } else if (xhr.status === 200) {
                self.container.innerHTML = '';
                var data = JSON.parse(xhr.responseText);
                Plotly.newPlot(self.container.id, data.data, data.layout, self.chartConfig)
            } else {
                self.container.innerHTML = '<p class="no-data"><span>Failed loading data</span></p>'
            }
        }
    }

    this.current_request = xhr
    xhr.send();
}

ChartMount.prototype.serializeFilter = function(obj) {
    var str = [];
    for (var p in obj) {
        if (obj.hasOwnProperty(p)) {
            str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
        }
    }
    return str.join("&");
}
