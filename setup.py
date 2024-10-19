from setuptools import setup

setup(
    name='splat',
    version='0.1',
    py_modules=['splat'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        splat=splat:cli
    ''',
)
