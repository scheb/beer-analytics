import {DetailList} from "./lists"
import {ChartContainer, RecipesContainer} from "./results"
import {SearchBox} from "./search"
import {Collapse, ScrollSpy, Tab} from "bootstrap"
import {Analyzer} from "./filtering";
import { registerLicense } from '@syncfusion/ej2-base';
import {InteractionElement} from "./interaction";

declare global {
    interface Window { _paq: any; }
}

registerLicense('Ngo9BigBOggjHTQxAR8/V1NHaF5cWWdCf1FpRmJGdld5fUVHYVZUTXxaS00DNHVRdkdnWXxeeHRQQmlcU010XEs=');

// Init navigation toggle
document.querySelectorAll('[data-bs-toggle="collapse"]')
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
    .forEach(recipesNode => new RecipesContainer(recipesNode))

// Init search boxes
document.querySelectorAll("form[data-search-target]")
    .forEach(formNode => new SearchBox(formNode))

// Init interaction tracking
document.querySelectorAll("[data-interaction]")
    .forEach(interactionNode => new InteractionElement(interactionNode))

// Init custom filtering
new Analyzer(() => {
    // When the result loads, remove active flags from navigation
    document.getElementById('top-navigation').querySelectorAll('.nav-link').forEach((element: Element) => {
        element.classList.remove('active')
    })
})

const toc = document.getElementById('toc-navigation');
if (toc) {
    new ScrollSpy(document.body, {
        target: toc,
        threshold: [0.01, 0.25, 0.5, 0.75, 1],  // Refresh calculations every quarter of a section
        rootMargin: "-70px 0px -25% 0px",  // Top: Account for sticky header, Bottom: Ignore the bottom 25% of the viewport
    })
}
