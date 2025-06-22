
export function formatScientific(num, max_digits) {
    const str = String(num);
    if (str.includes('E')) {
        const [mantissa, exponent] = str.split('E');
        if (mantissa.length > max_digits) {
            return mantissa.substring(0, max_digits) + '...' + 'E' + exponent;
        }
    } else {
        if (str.length > max_digits) {
            return str.substring(0, max_digits) + '...';
        }
    }
    return str;
}
