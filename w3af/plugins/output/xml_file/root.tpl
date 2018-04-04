<?xml version="1.0" encoding="utf-8"?>
<w3af-run start="{{ start_timestamp }}" start-long="{{ start_time_long }}" version="{{ xml_version }}">

    <w3af-version>{{ w3af_version }}</w3af-version>

    {{ scan_info | safe }}

    {{ scan_status | safe }}

    {% for finding in findings %}
        {{ finding | safe }}
    {% endfor %}

    {% for message, caller in errors %}
    <error caller="{{ caller | escape_attr }}">{{ message | escape_text }}</error>
    {% endfor %}
</w3af-run>
