import os

from jinja2 import Environment, FileSystemLoader
from w3af import ROOT_PATH


def render(template_name, context):
    """
    Render template with context

    :param template_name: string path to template, relative to templates folder
    :param context: dict with variables
    :return: compiled template string
    """
    path = os.path.join(ROOT_PATH, 'core/controllers/daemons/proxy/templates')
    env = Environment(loader=FileSystemLoader(path))

    template = env.get_template(template_name)
    return template.render(context)
