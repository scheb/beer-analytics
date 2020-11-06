import Tab from 'bootstrap/js/dist/tab'
import {DetailList} from "./lists"
import {Chart, Recipes} from "./results";

document.addEventListener("DOMContentLoaded", function() {
    // Init tabs
    document.querySelectorAll('.tabs')
        .forEach(tabNode => new Tab(tabNode))

    // Init detail lists
    document.querySelectorAll("dl.detail-info")
        .forEach(listNode => new DetailList(listNode))

    // Init charts
    document.querySelectorAll("[data-chart]")
        .forEach(chartNode => new Chart(chartNode))

    // Init recipes lists
    document.querySelectorAll("[data-recipes]")
        .forEach(recipesNode => new Recipes(recipesNode))
})
