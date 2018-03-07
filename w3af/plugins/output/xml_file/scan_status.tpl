<scan-status>
    <status>{{ status | escape_attr_val }}</status>
    <is-paused>{{ is_paused | escape_attr_val }}</is-paused>
    <is-running>{{ is_running | escape_attr_val }}</is-running>

    <active-plugin>
        <crawl>{{ active_crawl_plugin | escape_attr_val }}</crawl>
        <audit>{{ active_audit_plugin | escape_attr_val }}</audit>
    </active-plugin>

    <current-request>
        <crawl>{{ current_crawl_request | escape_attr_val }}</crawl>
        <audit>{{ current_audit_request | escape_attr_val }}</audit>
    </current-request>

    <queues>
        <crawl>
            <input-speed>{{ crawl_input_speed | escape_attr_val }}</input-speed>
            <output-speed>{{ crawl_output_speed | escape_attr_val }}</output-speed>
            <length>{{ crawl_queue_length | escape_attr_val }}</length>
        </crawl>

        <audit>
            <input-speed>{{ audit_input_speed | escape_attr_val }}</input-speed>
            <output-speed>{{ audit_output_speed | escape_attr_val }}</output-speed>
            <length>{{ audit_queue_length | escape_attr_val }}</length>
        </audit>
    </queues>

    <eta>
        <crawl>{{ crawl_eta | escape_attr_val }}</crawl>
        <audit>{{ audit_eta| escape_attr_val }}</audit>
    </eta>

    <rpm>{{ rpm | escape_attr_val }}</rpm>

    <total-urls>{{ total_urls | escape_attr_val }}</total-urls>
</scan-status>
