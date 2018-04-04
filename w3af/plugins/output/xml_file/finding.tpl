<vulnerability id="{{ id_list }}" method="{{ http_method | escape_attr }}" name="{{ name | escape_attr }}" plugin="{{ plugin_name }}" severity="{{ severity }}" url="{{ url | escape_attr }}" var="{{ var | escape_attr }}">
    <description>{{ description | escape_text }}</description>

    {% if long_description %}
    <long-description>{{ long_description | escape_text }}</long-description>
    <fix-guidance>{{ fix_guidance | escape_text }}</fix-guidance>
    <fix-effort>{{ fix_effort }}</fix-effort>
    <references>
        {% for reference in references %}
            <reference title="{{ reference.title | escape_attr }}" url="{{ reference.url | escape_attr }}" />
        {% endfor %}
    </references>
    {% endif %}

    <http-transactions>
        {% for transaction in http_transactions %}
            {{ transaction | safe }}
        {% endfor %}
    </http-transactions>
</vulnerability>
