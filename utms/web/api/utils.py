def format_scientific(num, max_digits):
    str_num = str(num)
    if 'E' in str_num:
        mantissa, exponent = str_num.split('E')
        if len(mantissa) > max_digits:
            return mantissa[:max_digits] + '...' + 'E' + exponent
    else:
        if len(str_num) > max_digits:
            return str_num[:max_digits] + '...'
    return str_num
