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

export function groupBy<T, K extends keyof any>(list: T[], getKey: (item: T) => K) {
    return list.reduce((previous, currentItem) => {
        const group = getKey(currentItem);
        if (!previous[group]) previous[group] = [];
        previous[group].push(currentItem);
        return previous;
    }, {} as Record<K, T[]>);
}

export function queryParamsToObject(entries: IterableIterator<[string, string]>) {
    const result: any = {}
    for (const [key, value] of entries) { // each 'entry' is a [key, value] tupple
        result[key] = value;
    }
    return result;
}
