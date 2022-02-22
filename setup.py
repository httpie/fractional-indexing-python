from pathlib import Path

from setuptools import setup

from fractional_indexing import __version__, __doc__, __licence__

ROOT = Path(__file__).parent


setup(
    name='fractional-indexing',
    description=__doc__.strip(),
    long_description=(ROOT / 'README.md').read_text().strip(),
    long_description_content_type='text/markdown',
    version=__version__,
    license=__licence__,
    url='https://github.com/httpie/fractional-indexing-python',
    py_modules=[
        'fractional_indexing',
    ],
    install_requires=[
        'setuptools',
    ],
    project_urls={
        'GitHub': 'https://github.com/httpie/fractional-indexing-python',
        'Twitter': 'https://twitter.com/httpie',
        'Discord': 'https://httpie.io/discord',
    },
)
