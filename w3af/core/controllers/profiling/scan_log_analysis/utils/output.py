def sort_by_value(a, b):
    return cmp(b[1], a[1])


class KeyValueOutput(object):
    def __init__(self, _function, title, values=None):
        self.function = _function
        self.title = title
        self.values = values if values is not None else dict()

    def set_title(self, title):
        self.title = title

    def set_values(self, values):
        self.values = values

    def to_json(self):
        return {self.function: {self.title: self.values}}

    def to_console(self):
        print('[%s] %s' % (self.function, self.title))

        if isinstance(self.values, dict):
            values_list = self.values.items()
            values_list.sort(sort_by_value)

            for key, value in values_list:
                print('    - %s: %s' % (key, value))

        elif isinstance(self.values, list):
            self.values.sort()

            for value in self.values:
                print('    - %s' % (value,))

        else:
            msg = 'Unsupported type found in to_console(): %s'
            raise Exception(msg % self.values.__class__.__name__)

        print('')


class ListOutput(object):
    def __init__(self, _function):
        self.function = _function
        self.kv_output_list = []

    def append(self, kv_output):
        self.kv_output_list.append(kv_output)

    def to_json(self):
        data = [{kv.title: kv.values} for kv in self.kv_output_list]
        return {self.function: data}

    def to_console(self):
        for kv in self.kv_output_list:
            kv.function = self.function
            kv.to_console()


class ListOutputItem(KeyValueOutput):
    def __init__(self, title, values=None):
        super(ListOutputItem, self).__init__(None, title, values)
        self.title = title
        self.values = values if values is not None else dict()
