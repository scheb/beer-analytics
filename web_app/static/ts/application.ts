import {DetailList} from "./lists"
import {Chart, Recipes} from "./results"
import {SearchBox} from "./search"
import {Collapse, Tab} from "bootstrap"
import {Slider} from '@syncfusion/ej2-inputs'
import {CheckBoxSelection, MultiSelect} from '@syncfusion/ej2-dropdowns'

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
        .forEach(chartNode => new Chart(chartNode))

    // Init recipes lists
    document.querySelectorAll("[data-recipes]")
        .forEach(recipesNode => new Recipes(recipesNode))

    // Init search boxes
    document.querySelectorAll("form[data-search-target]")
        .forEach(formNode => new SearchBox(formNode))

    // Init recipes lists
    document.querySelectorAll("[data-range-slider]")
        .forEach(function (container: HTMLElement) {
            let defaultObj: Slider = new Slider({
                // Set the initial range values for slider
                value: [30, 70],
                // Set the type to render range slider
                type: 'Range',
                // Initialize tooltip with placement and showOn
                tooltip: { isVisible: true, placement: 'Before', showOn: 'Auto' },
            })
            defaultObj.appendTo(container)
        })

    MultiSelect.Inject(CheckBoxSelection);

    let listObj1: MultiSelect = new MultiSelect({
        // set the country data to dataSource property
        mode: 'CheckBox',
        // set the placeholder to MultiSelect input element
        placeholder: 'Filter styles',
        // set true for enable the selectAll support.
        // showSelectAll: true,
        // set true for enable the dropdown icon.
        showDropDownIcon: true,
        // set the placeholder to MultiSelect filter input element
        filterBarPlaceholder: 'Search styles',
        // set the MultiSelect popup height
        popupHeight: '350px'
    })
    listObj1.appendTo('#styleSelect');
})
