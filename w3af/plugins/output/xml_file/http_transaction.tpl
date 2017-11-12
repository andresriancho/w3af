<http-transaction id="{{ id }}">

    <http-request>
        <status>{{ request.status }}</status>
        <headers>
            {% for field, content in request.headers.iteritems() %}
            <header>
                <field>{{ field }}</field>
                <content>{{ content }}</content>
            </header>
            {% endfor %}
        </headers>
        <body content-encoding="base64">{{ request.body }}</body>
    </http-request>

    <http-response>
        <status>{{ response.status }}</status>
        <headers>
            <header>
            {% for field, content in response.headers.iteritems() %}
            <header>
                <field>{{ field }}</field>
                <content>{{ content }}</content>
            </header>
            {% endfor %}
            </header>
        </headers>
        <body content-encoding="base64">{{ response.body }}</body>
    </http-response>

</http-transaction>