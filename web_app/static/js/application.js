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
        new ChartNavigation(navigation_id, function (filter) {
            var query = {}
            if (filter) {
                query['filter'] = filter
            }
            chart.load(query)
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

    this.container.classList.add('chart-loading')
    this.container.innerHTML = '<span></span>'

    var query_string = this.serializeFilter(query)
    var url = this.chartUrl + (query_string ? '?'+query_string : '')

    var self = this
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            self.current_request = null
            self.container.classList.remove('chart-loading')
            if (xhr.status === 204) {
                self.container.classList.add('chart-no-data')
                self.container.innerHTML = '<p>Not enough data</p>'
            } else if (xhr.status === 200) {
                self.container.innerHTML = ''
                var data = JSON.parse(xhr.responseText);
                Plotly.newPlot(self.container.id, data.data, data.layout, self.chartConfig)
            } else {
                self.container.classList.add('chart-no-data')
                self.container.innerHTML = '<p>Failed loading data</p>'
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

function ChartNavigation(navigation_id, on_select) {
    this.navigation = document.querySelector('#' + navigation_id)
    this.navigation.className = this.navigation.className.replace('d-none', '')

    // Update styling
    this.update_style()
    window.addEventListener("resize", this.update_style.bind(this))

    var navigation_tab_list = document.querySelectorAll('#' + navigation_id + ' a[data-toggle="tab"]')
    navigation_tab_list.forEach(function (tab) {
        tab.addEventListener('shown.bs.tab', function (e) {
            var filter = e.target.dataset['filter']
            on_select(filter)
        })
    })
}

ChartNavigation.prototype.update_style = function() {
    var nav_element = this.navigation.querySelector('.nav')
    nav_element.className = nav_element.className
        .replace('nav-tabs card-header-tabs', '')
        .replace('nav-pills card-header-pills', '')

    // Decide if to show tabs for pills
    if (nav_element.clientHeight > 50) {
        nav_element.className += " nav-pills card-header-pills"
    } else {
        nav_element.className += " nav-tabs card-header-tabs"
    }
}

function DetailList(element) {
    this.element = element
    this.update_first_elements()
    window.addEventListener("resize", this.update_first_elements.bind(this))
}

DetailList.prototype.update_first_elements = function() {
    var parent_left = this.element.offsetLeft
    console.log("Parent: "+parent_left)
    var previous_top = null
    this.element.querySelectorAll("dt").forEach(function (dt_element) {
        var first_in_line = (null === previous_top || dt_element.offsetTop > previous_top)
            && parent_left === dt_element.offsetLeft
        previous_top = dt_element.offsetTop

        dt_element.classList.remove('first-in-line')
        if (first_in_line) {
            dt_element.classList.add('first-in-line')
        }
    })
}

document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("dl.detail-info").forEach(function (element) {
        new DetailList(element)
    })
})
