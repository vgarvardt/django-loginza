from setuptools import setup, find_packages

setup(
    name = 'django-loginza',
    version = '0.3.3',
    author = 'Vladimir Garvardt',
    author_email = 'vgarvardt@gmail.com',
    description = 'Django application for Loginza service',
    url = 'https://github.com/vgarvardt/django-loginza',
    packages = find_packages(exclude=['test_project', 'test_project.*']),
    include_package_data = True,
    zip_safe = False,
    install_requires = ['Django']
)