function delay(fn: Function, ms: number) {
    let timer: any = null
    return function (...args: any) {
        clearTimeout(timer)
        timer = setTimeout(fn.bind(this, ...args), ms || 0)
    }
}

class SearchGroup {
    private readonly element: HTMLElement

    constructor(element: HTMLElement) {
        this.element = element
    }

    public isMatching(): boolean {
        // Has a matching search item contained
        return null !== this.element.querySelector('.search-item.search-match')
    }

    public refreshView(): void {
        if (this.isMatching()) {
            this.element.classList.add('search-match')
        } else {
            this.element.classList.remove('search-match')
        }
    }
}

class SearchItem {
    private readonly element: HTMLElement
    private matching: boolean = false
    private readonly term: string = ''

    constructor(element: HTMLElement) {
        this.element = element
        this.element.classList.add('search-item')

        let dataTerm = element.dataset['searchTerm'];
        if (undefined !== dataTerm) {
            this.term = dataTerm.trim().toLowerCase()
        }
    }

    public isMatching(): boolean {
        return this.matching
    }

    public applySearchTerm(term: string): void {
        this.matching = this.term.indexOf(term) >= 0
    }

    public refreshView(): void {
        if (this.isMatching()) {
            this.element.classList.add('search-match')
        } else {
            this.element.classList.remove('search-match')
        }
    }
}

export class SearchBox {
    private searchItems: SearchItem[];
    private searchGroups: SearchGroup[];
    private noResultElement: HTMLParagraphElement;
    private readonly searchItemsContainer: HTMLElement;
    private searchTerm: string;

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

        this.searchItemsContainer = document.getElementById(searchForm.dataset['searchTarget'])
        if (null === this.searchItemsContainer) {
            return
        }

        const searchItemElements = this.searchItemsContainer.querySelectorAll('[data-search-term]')
        this.searchItems = Array<SearchItem>()
        searchItemElements.forEach(function (elem: Element) {
            if (elem instanceof HTMLElement) {
                this.searchItems.push(new SearchItem(elem))
            }
        }, this)

        const searchGroupElements = this.searchItemsContainer.querySelectorAll('.search-group')
        this.searchGroups = Array<SearchGroup>()
        searchGroupElements.forEach(function (elem: Element) {
            if (elem instanceof HTMLElement) {
                this.searchGroups.push(new SearchGroup(elem))
            }
        }, this)

        this.appendNoResult();
        input.addEventListener('keyup', delay(this.onKeyUp.bind(this), 500))
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

        // Execute search, refresh search items view
        let hasAnyMatch = false
        this.searchItems.forEach(function (searchItem: SearchItem) {
            searchItem.applySearchTerm(this.searchTerm)
            searchItem.refreshView()
            hasAnyMatch = hasAnyMatch || searchItem.isMatching()
        }, this)

        // Refresh view of search groups
        this.searchGroups.forEach(function (searchGroup: SearchGroup): void {
            searchGroup.refreshView()
        })

        // Do we have any results? => Hide/display "no results"
        if (hasAnyMatch) {
            this.noResultElement.classList.add('d-none')
        } else {
            this.noResultElement.classList.remove('d-none')
        }
    }
}
