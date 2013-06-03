from distutils.core import setup

setup(
    name='Origami',
    version='0.0.3',
    author='Joe Cross',
    author_email='joe.mcross@gmail.com',
    packages=['origami'],
    url='https://github.com/numberoverzero/origami',
    license='LICENSE.txt',
    description='Lightweight bit packing for classes',
    long_description=open('README.rst').read(),
    install_requires=["bitstring"],
    requires=["bitstring"],
)
