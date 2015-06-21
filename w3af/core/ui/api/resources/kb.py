from flask import jsonify, request
from .. import app


@app.route('/kb/', methods=['GET'])
def list_kb():
    """
    List vulnerabilities stored in the KB

    Filters:

        * /kb/?name= returns only vulnerabilities which contain the specified
          string in the vulnerability name. (contains)

        * /kb/?location_a= returns only vulnerabilities which match the location
          (equals)

        * /kb/?location_b= returns only vulnerabilities which match the location
          (equals)

        * /kb/?url= returns only vulnerabilities for a specific URL (startswith)

    If more than one filter is specified they are combined using AND.

    :return: A JSON containing a list of:
        - KB resource URL (eg. /kb/3)
        - The KB id (eg. 3)
        - The vulnerability name
        - The vulnerability URL
        - Location A
        - Location B
    """
    raise NotImplementedError


@app.route('/kb/<int:vulnerability_id>', methods=['GET'])
def get_kb(vulnerability_id):
    """
    The whole information related to the specified vulnerability ID

    :param vulnerability_id: The vulnerability ID to query
    :return: All the vulnerability information
    """
    raise NotImplementedError
