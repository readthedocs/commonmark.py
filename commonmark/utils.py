def to_camel_case(snake_str):
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)
