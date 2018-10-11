from setuptools import setup, find_packages

setup(
    name             = 'pyAPT',
    version          = '0.2',
    packages         = find_packages(),

    install_requires = ['pylibftdi>=0.14'],

    package_data     = {'': ['99-libftdi.rules']},

    author           = 'Christoph Weinsheimer',
    author_email     = 'christoph.weinsheimer@desy.de',
    description      = 'Python3 Controller module for Thorlabs motorized stages',
    license          = 'MIT',
)
