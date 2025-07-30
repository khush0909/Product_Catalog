from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def url_params(context, request, key_to_change, new_value):
    query_params = request.GET.copy()
    if key_to_change in query_params:
        if isinstance(query_params.getlist(key_to_change), list) and key_to_change == 'brand':
            # Handle multiple values for 'brand' if it exists
            current_values = query_params.getlist(key_to_change)
            if new_value in current_values:
                current_values.remove(new_value)
            else:
                current_values.append(new_value)
            query_params.setlist(key_to_change, current_values)
        else:
            query_params[key_to_change] = new_value
    else:
        query_params[key_to_change] = new_value

    if new_value == '': # For clearing a specific parameter
        if key_to_change in query_params:
            del query_params[key_to_change]
    
    # Special handling for brand if it's an empty list after toggle
    if key_to_change == 'brand' and not query_params.getlist('brand'):
        if 'brand' in query_params:
            del query_params['brand']

    return f"?{query_params.urlencode()}"

@register.simple_tag(takes_context=True)
def url_params_current_except(context, request, *keys_to_exclude):
    query_params = request.GET.copy()
    for key in keys_to_exclude:
        if key in query_params:
            del query_params[key]
    return f"&{query_params.urlencode()}" if query_params else ""

# Helper to combine existing params with new ones, particularly for category links
@register.simple_tag(takes_context=True)
def url_params_with_all(context, request, new_key, new_value):
    query_params = request.GET.copy()
    # Remove page parameter when changing categories/filters to go back to page 1
    if 'page' in query_params:
        del query_params['page']

    # Handle brands (checkboxes)
    if new_key == 'brand':
        current_brands = query_params.getlist('brand')
        if new_value in current_brands:
            current_brands.remove(new_value)
        else:
            current_brands.append(new_value)
        query_params.setlist('brand', current_brands)
        if not current_brands: # If all brands are unselected, remove the parameter
            del query_params['brand']
    else:
        # For single value parameters like category or sort_by
        query_params[new_key] = new_value

    return f"?{query_params.urlencode()}" if query_params else ""