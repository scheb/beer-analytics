import Tab from 'bootstrap/js/dist/tab'
import {DetailList} from "./lists"
import {Chart, Recipes} from "./results";

document.addEventListener("DOMContentLoaded", function() {
    // Init tabs
    Array.from(document.querySelectorAll('.tabs'))
        .forEach(tabNode => new Tab(tabNode))

    // Init detail lists
    Array.from(document.querySelectorAll("dl.detail-info"))
        .forEach(listNode => new DetailList(listNode))

    // Init charts
    Array.from(document.querySelectorAll("[data-chart]"))
        .forEach(chartNode => new Chart(chartNode))

    // Init recipes lists
    Array.from(document.querySelectorAll("[data-recipes]"))
        .forEach(recipesNode => new Recipes(recipesNode))
})
