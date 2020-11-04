export class DetailList {
    element: HTMLElement;

    constructor(element: Element) {
        if (element instanceof HTMLElement) {
            this.element = element;
            this.flagFirstElements()
            window.addEventListener("resize", this.flagFirstElements.bind(this))
        }
    }

    private flagFirstElements(): void {
        const parentLeft: number = this.element.offsetLeft
        let previousTop: number = null

        this.element.querySelectorAll("dt").forEach(function (dtElement) {
            // Element is first in line when it's shifted downwards from the previous element and it's on the left edge
            const firstInLine = (null === previousTop || dtElement.offsetTop > previousTop)
                && parentLeft === dtElement.offsetLeft;

            dtElement.classList.remove('first-in-line');
            if (firstInLine) {
                dtElement.classList.add('first-in-line');
            }

            previousTop = dtElement.offsetTop;
        })
    }
}
