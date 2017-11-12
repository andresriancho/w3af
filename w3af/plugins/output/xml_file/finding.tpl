<vulnerability id="{{ id_list }}" method="{{ http_method }}" name="{{ name }}" plugin="{{ plugin_name }}" severity="{{ severity }}" url="{{ url }}" var="{{ var }}">
    <description>{{ description }}</description>

    {% if long_description %}
    <long-description>{{ long_description }}</long-description>
    <fix-guidance>{{ fix_guidance }}</fix-guidance>
    <fix-effort>{{ fix_effort }}</fix-effort>
    <references>
        {% for reference in references %}
            <reference title="{{ reference.title }}" url="{{ reference.url }}" />
        {% endfor %}
    </references>
    {% endif %}

    <http-transactions>
        {% for transaction in http_transactions %}
            {{ transaction | safe }}
        {% endfor %}
    </http-transactions>
</vulnerability>
