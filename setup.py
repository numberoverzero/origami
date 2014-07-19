from setuptools import setup
import io
import os

here = os.path.abspath(os.path.dirname(__file__))


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.rst')

setup(
    name='Origami',
    version='0.2.0',
    author='Joe Cross',
    author_email='joe.mcross@gmail.com',
    packages=['origami'],
    url='https://github.com/numberoverzero/origami',
    license='LICENSE.txt',
    description='Lightweight bit packing for classes',
    long_description=long_description,
    install_requires=["bitstring"]
)
