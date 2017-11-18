<http-transaction id="{{ id }}">

    <http-request>
        <status>{{ request.status }}</status>
        <headers>
            {% for field, content in request.headers.iteritems() %}
            <header field="{{ field | escape_attr_val }}" content="{{ content | escape_attr_val }}" />
            {% endfor %}
        </headers>
        <body content-encoding="base64">{{ request.body }}</body>
    </http-request>

    <http-response>
        <status>{{ response.status }}</status>
        <headers>
            {% for field, content in response.headers.iteritems() %}
            <header field="{{ field | escape_attr_val }}" content="{{ content | escape_attr_val }}" />
            {% endfor %}
        </headers>
        <body content-encoding="base64">{{ response.body }}</body>
    </http-response>

</http-transaction>