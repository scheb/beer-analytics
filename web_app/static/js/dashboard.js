/* globals Chart:false, feather:false */

function display_graph(container_id, chart_url, config={}) {
    let container = document.getElementById(container_id)
    if (!container)
    {
        return
    }

    container.innerHTML = '<div class="chart-loading"><span></span></div>'

    let defaultConfig = {responsive: true, displayModeBar: true}
    let mergedConfig = {...defaultConfig, ...config};

    let xhr = new XMLHttpRequest();
    xhr.open("GET", chart_url, true);
    xhr.onreadystatechange = function ()
    {
        if (xhr.readyState === 4)
        {
            if (xhr.status === 204)
            {
                document.getElementById(container_id).innerHTML = '<p class="no-data"><span>No data</span></p>'
            }
            else if (xhr.status === 200)
            {
                container.innerHTML = '';
                let data = JSON.parse(xhr.responseText);
                Plotly.newPlot(container_id, data.data, data.layout, mergedConfig)
            }
        }
    }
    xhr.send();
}
