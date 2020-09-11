/* globals Chart:false, feather:false */

function display_graph(container_id, chart_url, config={}) {
    if (!document.getElementById(container_id))
    {
        return
    }

    let defaultConfig = {responsive: true, displayModeBar: true}
    let mergedConfig = {...defaultConfig, ...config};

    let xhr = new XMLHttpRequest();
    xhr.open("GET", chart_url, true);
    xhr.onreadystatechange = function ()
    {
        if (xhr.readyState === 4 && xhr.status === 200)
        {
            let data = JSON.parse(xhr.responseText);
            Plotly.newPlot(container_id, data.data, data.layout, mergedConfig)
        }
    }
    xhr.send();
}
