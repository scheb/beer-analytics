export function trackSearch(searchTerm: string, searchType: string, numResults: number): void {
    let payload = ['trackSiteSearch', searchTerm, searchType, numResults];
    if (typeof window._paq === "object") {
        window._paq.push(payload);
    }
    // console.log(payload)
}

export function trackInteraction(category: string, action: string, name: string = '', value: number|string = ''): void {
    let payload = ['trackEvent', category, action, name, value];
    if (typeof window._paq === "object") {
        window._paq.push(payload);
    }
    // console.log(payload)
}

export class InteractionElement {
    private readonly category: string
    private readonly action: string
    private readonly name: string

    constructor(element: Element) {
        if (!(element instanceof HTMLElement)) {
            return
        }
        if (undefined === element.dataset['interaction']) {
            return
        }

        let parts = element.dataset['interaction'].split(":")
        if (parts.length < 2) {
            return
        }

        this.category = parts[0]
        this.action = parts[1]
        this.name = parts[2] ?? ''

        // Take the label from thing
        if (this.name === "$label") {
            this.name = element.innerText
        }

        element.addEventListener("click", () => {
            trackInteraction(this.category, this.action, this.name)
        })
    }
}
