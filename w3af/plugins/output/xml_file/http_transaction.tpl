<http-transaction id="{{ id }}">

    <http-request>
        <status>{{ request.status | escape_text }}</status>
        <headers>
            {% for field, content in request.headers.iteritems() %}
            <header field="{{ field | escape_attr }}" content="{{ content | escape_attr }}" />
            {% endfor %}
        </headers>
        <body content-encoding="base64">{{ request.body }}</body>
    </http-request>

    <http-response>
        <status>{{ response.status | escape_text }}</status>
        <headers>
            {% for field, content in response.headers.iteritems() %}
            <header field="{{ field | escape_attr }}" content="{{ content | escape_attr }}" />
            {% endfor %}
        </headers>
        <body content-encoding="base64">{{ response.body }}</body>
    </http-response>

</http-transaction>