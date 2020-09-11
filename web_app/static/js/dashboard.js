/* globals Chart:false, feather:false */

(function () {
    'use strict'
    feather.replace()
})()

function display_graph(container_id, chart_url) {
    if (!document.getElementById(container_id))
    {
        return
    }

    let xhr = new XMLHttpRequest();
    xhr.open("GET", chart_url, true);
    xhr.onreadystatechange = function ()
    {
        if (xhr.readyState === 4 && xhr.status === 200)
        {
            let data = JSON.parse(xhr.responseText);
            Plotly.newPlot(container_id, data.data, data.layout, {responsive: true})
        }
    }
    xhr.send();
}
