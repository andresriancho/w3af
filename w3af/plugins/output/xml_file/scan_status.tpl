<scan-status>
    <status>{{ status | escape_text }}</status>
    <is-paused>{{ is_paused | escape_text }}</is-paused>
    <is-running>{{ is_running | escape_text }}</is-running>

    <active-plugin>
        <crawl>{{ active_crawl_plugin | escape_text }}</crawl>
        <audit>{{ active_audit_plugin | escape_text }}</audit>
    </active-plugin>

    <current-request>
        <crawl>{{ current_crawl_request | escape_text }}</crawl>
        <audit>{{ current_audit_request | escape_text }}</audit>
    </current-request>

    <queues>
        <crawl>
            <input-speed>{{ crawl_input_speed | escape_text }}</input-speed>
            <output-speed>{{ crawl_output_speed | escape_text }}</output-speed>
            <length>{{ crawl_queue_length | escape_text }}</length>
            <processed-tasks>{{ crawl_queue_processed_tasks | escape_text }}</processed-tasks>
        </crawl>

        <audit>
            <input-speed>{{ audit_input_speed | escape_text }}</input-speed>
            <output-speed>{{ audit_output_speed | escape_text }}</output-speed>
            <length>{{ audit_queue_length | escape_text }}</length>
            <processed-tasks>{{ audit_queue_processed_tasks | escape_text }}</processed-tasks>
        </audit>

        <grep>
            <input-speed>{{ grep_input_speed | escape_text }}</input-speed>
            <output-speed>{{ grep_output_speed | escape_text }}</output-speed>
            <length>{{ grep_queue_length | escape_text }}</length>
            <processed-tasks>{{ grep_queue_processed_tasks | escape_text }}</processed-tasks>
        </grep>
    </queues>

    <eta>
        <crawl>{{ crawl_eta | escape_text }}</crawl>
        <audit>{{ audit_eta | escape_text }}</audit>
        <grep>{{ grep_eta | escape_text }}</grep>
        <all>{{ all_eta | escape_text }}</all>
    </eta>

    <rpm>{{ rpm | escape_text }}</rpm>
    <sent-request-count>{{ sent_request_count | escape_text }}</sent-request-count>
    <progress>{{ progress | escape_text }}</progress>

    <total-urls>{{ total_urls | escape_text }}</total-urls>
    <known-urls>

        {%- for url_node, children in known_urls.iteritems() recursive %}
            {%- if children -%}
                {{ "\n"|indent(loop.depth * 4, True, True) }}<node url="{{ url_node.path | escape_attr }}" exists="{{ url_node.is_leaf | escape_attr }}">
                {{ loop(children.iteritems()) }}
                {{ "\n"|indent(loop.depth * 4, True, True) }}</node>
            {%- else %}
                {{ "\n"|indent(loop.depth * 4, True, True) }}<node url="{{ url_node.path | escape_attr }}" exists="{{ url_node.is_leaf | escape_attr }}" />
            {%- endif %}
        {%- endfor %}

    </known-urls>
</scan-status>
