export function delay(fn: Function, ms: number) {
    let timer: any = null
    return function (...args: any) {
        clearTimeout(timer)
        timer = setTimeout(fn.bind(this, ...args), ms || 0)
    }
}

export function intersect<T>(array1: Array<T>, array2: Array<T>): Array<T> {
    return array1.filter(function(n: T): boolean {
        return array2.indexOf(n) !== -1;
    }, this)
}
