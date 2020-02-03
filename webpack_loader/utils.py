from importlib import import_module
from django.conf import settings
from django.core.files.storage import get_storage_class
from .config import load_config


_loaders = {}
media_storage = get_storage_class(settings.STATICFILES_STORAGE)()


def import_string(dotted_path):
    '''
    This is a rough copy of django's import_string, which wasn't introduced until Django 1.7

    Once this package's support for Django 1.6 has been removed, this can be safely replaced with
    `from django.utils.module_loading import import_string`
    '''
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
        module = import_module(module_path)
        return getattr(module, class_name)
    except (ValueError, AttributeError, ImportError):
        raise ImportError('%s doesn\'t look like a valid module path' % dotted_path)


def get_loader(config_name):
    if config_name not in _loaders:
        config = load_config(config_name)
        loader_class = import_string(config['LOADER_CLASS'])
        _loaders[config_name] = loader_class(config_name, config)
    return _loaders[config_name]


def _filter_by_extension(bundle, extension):
    '''Return only files with the given extension'''
    for chunk in bundle:
        if chunk['name'].endswith('.{0}'.format(extension)):
            yield chunk


def _get_bundle(bundle_name, extension, config):
    bundle = get_loader(config).get_bundle(bundle_name)
    if extension:
        bundle = _filter_by_extension(bundle, extension)
    return bundle


def get_files(bundle_name, extension=None, config='DEFAULT'):
    '''Returns list of chunks from named bundle'''
    return list(_get_bundle(bundle_name, extension, config))


def get_as_tags(bundle_name, extension=None, config='DEFAULT', attrs=''):
    '''
    Get a list of formatted <script> & <link> tags for the assets in the
    named bundle.

    :param bundle_name: The name of the bundle
    :param extension: (optional) filter by extension, eg. 'js' or 'css'
    :param config: (optional) the name of the configuration
    :return: a list of formatted tags as strings
    '''

    bundle = _get_bundle(bundle_name, extension, config)
    tags = []
    for chunk in bundle:
        url = self.get_chunk_url(chunk)

        if chunk['name'].endswith(('.js', '.js.gz')):
            tags.append((
                '<script type="text/javascript" src="{0}" {1}></script>'
            ).format(media_storage.url(url), attrs))
        elif chunk['name'].endswith(('.css', '.css.gz')):
            tags.append((
                '<link type="text/css" href="{0}" rel="stylesheet" {1}/>'
            ).format(media_storage.url(), attrs))
    return tags
    
    def get_chunk_url(chunk):
        """
            Remove file routes from chunks

            url = /tmp/demo/test.jpg

            return: test.jpg
        """

        if not '/' in chunk['url']:
            return chunk['url']

        reverse = chunk['url'][len(chunk['url'])::-1]
        index = reverse.index('/')

        return reverse[0:index][len(reverse)::-1]



def get_static(asset_name, config='DEFAULT'):
    '''
    Equivalent to Django's 'static' look up but for webpack assets.

    :param asset_name: the name of the asset
    :param config: (optional) the name of the configuration
    :return: path to webpack asset as a string
    '''
    return "{0}{1}".format(
        get_loader(config).get_assets().get(
            'publicPath', getattr(settings, 'STATIC_URL')
        ),
        asset_name
    )
