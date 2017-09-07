from setuptools import setup, find_packages

setup(
    name='odooku-graphql',
    version='10.0.1000',
    url='https://github.com/odooku/odooku-graphql',
    author='Raymond Reggers - Adaptiv Design',
    author_email='raymond@adaptiv.nl',
    description=('Odooku Graphql'),
    license='Apache Software License',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    namespace_packages=[
        'odooku_addons',
        'odooku_patches'
    ],
    install_requires=[
        'odooku>=10.0.0,<11.0.0',
        'graphene>=2.0.dev',
        'singledispatch==3.4.0.3',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: Apache Software License',
    ],
)
