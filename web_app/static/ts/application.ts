import Tab from 'bootstrap/js/dist/tab'
import Collapse from "bootstrap/js/dist/collapse";
import {DetailList} from "./lists"
import {Chart, Recipes} from "./results"
import {SearchBox} from "./search"

document.addEventListener("DOMContentLoaded", function() {
    // Init navigation toggle
    document.querySelectorAll('[data-toggle="collapse"]')
        .forEach(tabNode => new Collapse(tabNode))

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

    // Init search boxes
    document.querySelectorAll("form[data-search-target]")
        .forEach(formNode => new SearchBox(formNode))
})
