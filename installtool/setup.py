#from ez_setup import use_setuptools
#use_setuptools()
from setuptools import setup, find_packages
with open("README.md","r") as fh:
    long_description = fh.read()
setup(
    name = "installtool",
    version = "0.95",
    packages = find_packages(),
    py_modules = ['mylog', 'inspect', 'concurrent.futures'],
    install_requires = ['jira_python>=0.13', 'PyYAML'],
    python_requires='>=3',

    # metadata for upload to PyPI
    author = "Geoff White",
    author_email = "geoffw@ambientnetworks.org",
    description = "Perform remote installs using yaml manifests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/l0r3zz/public/installtool",
    license = "Apache 2.0",
    keywords = "install automation remote yaml ",
    classifiers=[
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 4 - Beta',

    # Indicate who your project is intended for
    'Intended Audience :: DevOps',
    'Topic :: Software Development :: Build Tools',

    # Pick your license as you wish (should match "license" above)
     'License :: OSI Approved :: Apache 2.0',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    ],
    entry_points = {
        'console_scripts': [
            'installtool = installtool:main',
            ]
    }
)
