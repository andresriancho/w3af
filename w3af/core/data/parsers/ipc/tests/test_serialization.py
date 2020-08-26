import os
import shutil
import tempfile

from mock import MagicMock

from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.sgml import Tag
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.ipc.serialization import FileSerializer
from w3af.core.data.url.HTTPResponse import HTTPResponse


def create_http_response(body):
    url = URL('http://localhost')
    return HTTPResponse(
        200,
        body,
        Headers(),
        url,
        url,
    )


class TestFileSerializer:
    def setup_method(self):
        self.temp_directory = tempfile.gettempdir() + '/w3af-test'
        os.mkdir(self.temp_directory)
        self.serializer = FileSerializer(file_directory=self.temp_directory)

    def teardown_method(self):
        shutil.rmtree(self.temp_directory)

    def test_it_uses_default_directory_if_custom_is_not_provided(self):
        serializer = FileSerializer()
        assert serializer.file_directory

    def test_it_returns_filename_on_save(self):
        http_response = MagicMock()
        http_response.to_dict = MagicMock(return_value={'mock-key': 'mock-value'})
        filename = self.serializer.save_http_response(http_response)
        assert 'w3af-http-' in filename

    def test_it_can_save_two_different_responses_and_get_them_back(self):
        http_response1 = create_http_response('value1')
        http_response2 = create_http_response('value2')

        filename1 = self.serializer.save_http_response(http_response1)
        filename2 = self.serializer.save_http_response(http_response2)

        loaded_response1 = self.serializer.load_http_response(filename1)
        loaded_response2 = self.serializer.load_http_response(filename2)

        assert loaded_response1.body == 'value1'
        assert loaded_response2.body == 'value2'

    def test_it_can_save_and_load_tags(self):
        tags = [Tag(i, i) for i in range(3)]
        tags_id = self.serializer.save_tags(tags)
        loaded_tags = self.serializer.load_tags(tags_id)
        assert loaded_tags == tags
