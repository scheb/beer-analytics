import {DetailList} from "./lists"
import {ChartContainer, Recipes} from "./results"
import {SearchBox} from "./search"
import {Collapse, Tab} from "bootstrap"
import {Analyzer} from "./filtering";

document.addEventListener("DOMContentLoaded", function() {
    // Init navigation toggle
    document.querySelectorAll('[data-toggle="collapse"]')
        .forEach(toggleNode => new Collapse(toggleNode))

    // Init tabs
    document.querySelectorAll('.tabs')
        .forEach(tabNode => new Tab(tabNode))

    // Init detail lists
    document.querySelectorAll("dl.detail-info")
        .forEach(listNode => new DetailList(listNode))

    // Init charts
    document.querySelectorAll("[data-chart]")
        .forEach(chartNode => new ChartContainer(chartNode))

    // Init recipes lists
    document.querySelectorAll("[data-recipes]")
        .forEach(recipesNode => new Recipes(recipesNode))

    // Init search boxes
    document.querySelectorAll("form[data-search-target]")
        .forEach(formNode => new SearchBox(formNode))

    // Init custom filtering
    new Analyzer(() => {
        // When the result loads, remove active flags from navigation
        document.getElementById('top-navigation').querySelectorAll('.nav-link').forEach((element: Element) => {
            element.classList.remove('active')
        })
    })
})
