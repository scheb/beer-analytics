import {delay} from "./utils";

declare global {
    interface Window { _paq: any; }
}

abstract class SearchResultElement {
    public readonly element: HTMLElement

    constructor(element: HTMLElement) {
        this.element = element
    }

    public abstract isShown(): boolean

    public refreshView(): void {
        if (this.isShown()) {
            this.element.classList.add('search-show')
        } else {
            this.element.classList.remove('search-show')
        }
    }
}

class SearchableGroup extends SearchResultElement {
    public isShown(): boolean {
        // Has a matching search item contained
        return null !== this.element.querySelector('.search-item.search-show')
    }
}

class SearchableItem extends SearchResultElement {
    private readonly searchableString: string = ''
    private searchTermIsMatching: boolean = false
    private children: Set<SearchableItem> = new Set<SearchableItem>()
    private parents: Set<SearchableItem> = new Set<SearchableItem>()

    constructor(element: HTMLElement) {
        super(element)
        this.element.classList.add('search-item')

        let dataTerm = element.dataset['searchTerm'];
        if (undefined !== dataTerm) {
            this.searchableString = dataTerm.trim().toLowerCase()
        }
    }

    public addChildItem(searchItem: SearchableItem) {
        this.children.add(searchItem)
    }

    public addParentItem(searchItem: SearchableItem) {
        this.parents.add(searchItem)
    }

    public applySearchTerm(searchTerms: string[]): void {
        if (searchTerms.length == 0) {
            this.searchTermIsMatching = false
            return;
        }

        this.searchTermIsMatching = true
        searchTerms.forEach((singleTerm: string) => {
            this.searchTermIsMatching = this.searchTermIsMatching && this.searchableString.indexOf(singleTerm) >= 0
        })
    }

    public isSearchTermMatching(): boolean {
        return this.searchTermIsMatching
    }

    public isShown(): boolean {
        if (this.searchTermIsMatching) {
            return true
        }

        if (this.childrenIsTermMatching()) {
            return true
        }

        return this.parentsIsTermMatching()
    }

    private childrenIsTermMatching(): boolean {
        return [...this.children].reduce((result, searchItem: SearchableItem) => result || searchItem.isSearchTermMatching(), false);
    }

    private parentsIsTermMatching(): boolean {
        return [...this.parents].reduce((result, searchItem: SearchableItem) => result || searchItem.isSearchTermMatching(), false);
    }

    public getNumberOfMatches(): number {
        let result = this.searchTermIsMatching ? 1 : 0
        return [...this.children].reduce((result, searchItem: SearchableItem) => result + searchItem.getNumberOfMatches(), result);
    }
}

export class SearchBox {
    private readonly searchType: string
    private readonly searchItems: Map<string, SearchableItem>
    private readonly searchGroups: SearchableGroup[]
    private readonly searchItemsContainer: HTMLElement
    private noResultElement: HTMLParagraphElement
    private rawSearchTerm: string
    private searchTerms: string[]

    constructor(searchForm: Element) {
        if (!(searchForm instanceof HTMLFormElement)) {
            return
        }
        if (undefined === searchForm.dataset['searchTarget']) {
            return
        }

        this.searchType = searchForm.dataset['searchType']
        const input = searchForm.querySelector('input[type="search"]')
        if (!(input instanceof HTMLInputElement)) {
            return
        }
        input.focus()

        this.searchItemsContainer = document.getElementById(searchForm.dataset['searchTarget'])
        if (null === this.searchItemsContainer) {
            return
        }

        // Collect all search terms
        let idInc = 0
        const searchItemElements = this.searchItemsContainer.querySelectorAll('[data-search-term]')
        this.searchItems = new Map<string, SearchableItem>()
        searchItemElements.forEach(function (elem: Element) {
            if (elem instanceof HTMLElement) {
                // Assign a unique id, if there is none
                if (null === elem.id || '' === elem.id) {
                    elem.id = 'search-'+(++idInc)
                }
                this.searchItems.set(elem.id, new SearchableItem(elem))
            }
        }, this)

        // Add SearchItems as children to their respective parent SearchItems and reverse
        this.searchItems.forEach(function (searchItem: SearchableItem): void {
            let node: Node = searchItem.element;
            while (node !== document) {
                node = node.parentNode
                if (node instanceof HTMLElement && this.searchItems.has(node.id)) {
                    let parentSearchItem = this.searchItems.get(node.id)
                    parentSearchItem.addChildItem(searchItem)
                    searchItem.addParentItem(parentSearchItem)
                }
            }
        }, this)

        // Collect all search group elements (only shown when they contain a matching search term)
        const searchGroupElements = this.searchItemsContainer.querySelectorAll('.search-group')
        this.searchGroups = Array<SearchableGroup>()
        searchGroupElements.forEach(function (elem: Element) {
            if (elem instanceof HTMLElement) {
                this.searchGroups.push(new SearchableGroup(elem))
            }
        }, this)

        this.appendNoResult();
        input.addEventListener('input', delay(this.onInput.bind(this), 800))
        if (input.value.length > 0) {
            this.search(input.value)
        }
    }

    private onInput(evt: KeyboardEvent): void {
        if (evt.target instanceof HTMLInputElement) {
            this.search(evt.target.value)
        }
    }

    private search(searchTerm: string): void {
        const splitter = /[\s_\-.,;:]+/g
        this.rawSearchTerm = searchTerm
        this.searchTerms = searchTerm.replace(splitter, " ").trim().toLowerCase().split(" ")
        this.refreshView()
    }

    private appendNoResult(): void {
        this.noResultElement = document.createElement('p')
        this.noResultElement.classList.add('search-no-result')
        this.noResultElement.classList.add('d-none')
        this.noResultElement.appendChild(document.createTextNode('No result'))
        this.searchItemsContainer.appendChild(this.noResultElement)
    }

    private refreshView() {
        // Do we have a search term? => Flag view as "filtered"
        if (this.searchTerms.length > 0) {
            this.searchItemsContainer.classList.add('search-filtered')
        } else {
            this.searchItemsContainer.classList.remove('search-filtered')
        }

        // Execute search
        this.searchItems.forEach(function (searchItem: SearchableItem) {
            searchItem.applySearchTerm(this.searchTerms)
        }, this)

        // refresh search items view
        let hasAnyMatch = false
        let numMatches = 0
        this.searchItems.forEach(function (searchItem: SearchableItem) {
            searchItem.refreshView()
            hasAnyMatch = hasAnyMatch || searchItem.isShown()
            numMatches += searchItem.getNumberOfMatches()
        }, this)

        // Refresh view of search groups
        this.searchGroups.forEach(function (searchGroup: SearchableGroup): void {
            searchGroup.refreshView()
        })

        // Do we have any results? => Hide/display "no results"
        if (hasAnyMatch || this.searchTerms.length === 0) {
            this.noResultElement.classList.add('d-none')
        } else {
            this.noResultElement.classList.remove('d-none')
        }

        // Tracking
        if (this.searchTerms.length > 0) {
            this.trackSearch(this.rawSearchTerm, numMatches)
        }
    }

    private trackSearch(searchTerm: string, numResults: number) {
        // console.log(['trackSiteSearch', searchTerm, this.searchType, numResults])
        if (typeof window._paq === "object") {
            window._paq.push(['trackSiteSearch', searchTerm, this.searchType, numResults]);
        }
    }
}
