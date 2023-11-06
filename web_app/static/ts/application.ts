import {DetailList} from "./lists"
import {ChartContainer, Recipes} from "./results"
import {SearchBox} from "./search"
import {Collapse, Tab} from "bootstrap"
import {Analyzer} from "./filtering";
import { registerLicense } from '@syncfusion/ej2-base';
import {InteractionElement} from "./interaction";

declare global {
    interface Window { _paq: any; }
}

registerLicense('Mgo+DSMBaFt+QHFqVkNrXVNbdV5dVGpAd0N3RGlcdlR1fUUmHVdTRHRcQlljTn9TdUBjXnxfeHM=;Mgo+DSMBPh8sVXJ1S0d+X1RPd11dXmJWd1p/THNYflR1fV9DaUwxOX1dQl9gSXpTcURjWnped3dWRGc=;ORg4AjUWIQA/Gnt2VFhhQlJBfV5AQmBIYVp/TGpJfl96cVxMZVVBJAtUQF1hSn5XdkJiWXxbcHNWQmVb;MTY1MjM3OEAzMjMxMmUzMTJlMzMzNVRUbXVSQWxmbTFXSEhFSm02aGpMWGFKekZWV09DMllKVjRsRDV2NEI4Y1E9;MTY1MjM3OUAzMjMxMmUzMTJlMzMzNUZMTityYmR0MFBmU21EUzEvdU5UOVpCOVY5cDVhME1kMFRYTUhsWFpHRnM9;NRAiBiAaIQQuGjN/V0d+XU9Hc1RDX3xKf0x/TGpQb19xflBPallYVBYiSV9jS31TckVkWH9ddXRSQmFdVg==;MTY1MjM4MUAzMjMxMmUzMTJlMzMzNUdmTnpNbkFFSEZYRS9CTXdGVFdFdCtXN3Y0WlJ2MnhxVDZ4Q1p4TUNNZkU9;MTY1MjM4MkAzMjMxMmUzMTJlMzMzNUY1U09VSmZWWjJFOHpkVUVsSnNVZ2owL29vbUZ4Snh0aHEwTHI4Vm45N3c9;Mgo+DSMBMAY9C3t2VFhhQlJBfV5AQmBIYVp/TGpJfl96cVxMZVVBJAtUQF1hSn5XdkJiWXxbcHNRQWhb;MTY1MjM4NEAzMjMxMmUzMTJlMzMzNU9mSzg4ajZnRHJKSG12TlV3Y1huVFVEZnVWYmhHZFo5alBkYnNYcndOcUE9;MTY1MjM4NUAzMjMxMmUzMTJlMzMzNW5VeS9idHNmZjFrS1BTeEsvNFhzSUQxOEk2cnF5ZGpRcldMRzlrbmZaT0k9;MTY1MjM4NkAzMjMxMmUzMTJlMzMzNUdmTnpNbkFFSEZYRS9CTXdGVFdFdCtXN3Y0WlJ2MnhxVDZ4Q1p4TUNNZkU9');

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
    .forEach(recipesNode => new Recipes(recipesNode))

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
