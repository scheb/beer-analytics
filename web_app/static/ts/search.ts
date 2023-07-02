import {delay} from "./utils";

abstract class SearchElement {
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

class SearchGroup extends SearchElement {
    public isShown(): boolean {
        // Has a matching search item contained
        return null !== this.element.querySelector('.search-item.search-show')
    }
}

class SearchItem extends SearchElement {
    private readonly term: string = ''
    private termMatching: boolean = false
    private children: Set<SearchItem> = new Set<SearchItem>()
    private parents: Set<SearchItem> = new Set<SearchItem>()

    constructor(element: HTMLElement) {
        super(element)
        this.element.classList.add('search-item')

        let dataTerm = element.dataset['searchTerm'];
        if (undefined !== dataTerm) {
            this.term = dataTerm.trim().toLowerCase()
        }
    }

    public addChildItem(searchItem: SearchItem) {
        this.children.add(searchItem)
    }

    public addParentItem(searchItem: SearchItem) {
        this.parents.add(searchItem)
    }

    public applySearchTerm(term: string): void {
        if (term.length > 0) {
            this.termMatching = this.term.indexOf(term) >= 0
        } else {
            this.termMatching = false
        }
    }

    public isTermMatching(): boolean {
        return this.termMatching
    }

    public isShown(): boolean {
        if (this.termMatching) {
            return true
        }

        if (this.childrenIsTermMatching()) {
            return true
        }

        return this.parentsIsTermMatching()
    }

    private childrenIsTermMatching() {
        return [...this.children].reduce((result, searchItem: SearchItem) => result || searchItem.isTermMatching(), false);
    }

    private parentsIsTermMatching() {
        return [...this.parents].reduce((result, searchItem: SearchItem) => result || searchItem.isTermMatching(), false);
    }
}

export class SearchBox {
    private readonly searchItems: Map<string, SearchItem>
    private readonly searchGroups: SearchGroup[]
    private readonly searchItemsContainer: HTMLElement
    private noResultElement: HTMLParagraphElement
    private searchTerm: string

    constructor(searchForm: Element) {
        if (!(searchForm instanceof HTMLFormElement)) {
            return
        }
        if (undefined === searchForm.dataset['searchTarget']) {
            return
        }
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
        this.searchItems = new Map<string, SearchItem>()
        searchItemElements.forEach(function (elem: Element) {
            if (elem instanceof HTMLElement) {
                // Assign a unique id, if there is none
                if (null === elem.id || '' === elem.id) {
                    elem.id = 'search-'+(++idInc)
                }
                this.searchItems.set(elem.id, new SearchItem(elem))
            }
        }, this)

        // Add SearchItems as children to their respective parent SearchItems and reverse
        this.searchItems.forEach(function (searchItem: SearchItem): void {
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
        this.searchGroups = Array<SearchGroup>()
        searchGroupElements.forEach(function (elem: Element) {
            if (elem instanceof HTMLElement) {
                this.searchGroups.push(new SearchGroup(elem))
            }
        }, this)

        this.appendNoResult();
        input.addEventListener('input', delay(this.onKeyUp.bind(this), 500))
        if (input.value.length > 0) {
            this.search(input.value)
        }
    }

    private onKeyUp(evt: KeyboardEvent): void {
        if (evt.target instanceof HTMLInputElement) {
            this.search(evt.target.value)
        }
    }

    private search(searchTerm: string): void {
        this.searchTerm = searchTerm.trim().toLowerCase()
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
        if (this.searchTerm.length > 0) {
            this.searchItemsContainer.classList.add('search-filtered')
        } else {
            this.searchItemsContainer.classList.remove('search-filtered')
        }

        // Execute search
        this.searchItems.forEach(function (searchItem: SearchItem) {
            searchItem.applySearchTerm(this.searchTerm)
        }, this)

        // refresh search items view
        let hasAnyMatch = false
        this.searchItems.forEach(function (searchItem: SearchItem) {
            searchItem.refreshView()
            hasAnyMatch = hasAnyMatch || searchItem.isShown()
        }, this)

        // Refresh view of search groups
        this.searchGroups.forEach(function (searchGroup: SearchGroup): void {
            searchGroup.refreshView()
        })

        // Do we have any results? => Hide/display "no results"
        if (hasAnyMatch || this.searchTerm.length === 0) {
            this.noResultElement.classList.add('d-none')
        } else {
            this.noResultElement.classList.remove('d-none')
        }
    }
}
