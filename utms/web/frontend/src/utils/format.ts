export function formatScientific(num: string | number, maxDigits: number): string {
    const str = String(num);
    if (str.includes('E')) {
        const [mantissa, exponent] = str.split('E');
        if (mantissa.length > maxDigits) {
            return mantissa.substring(0, maxDigits) + '...' + 'E' + exponent;
        }
    } else {
        if (str.length > maxDigits) {
            return str.substring(0, maxDigits) + '...';
        }
    }
    return str;
}
