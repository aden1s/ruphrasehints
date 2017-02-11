from setuptools import setup, find_packages

requirements = [l.strip() for l in open('requirements.txt').readlines()]

setup(
     name='ruphrasehints',
     version='0.1',
     install_requires = requirements,
     packages = find_packages(),
     include_package_data = True, 
     author = 'Denis Aksenenko',
     author_email = 'aksenenkodenis@gmail.com',
     description = 'Search phrase and wordforms in text and replace it with user hint',
     license = '', 
     keywords = 'hints',
     url='https://github.com/aden1s/ru-phrasehints',
     )
