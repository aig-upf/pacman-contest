from setuptools import setup, find_packages
import os

def main():
    setup(
        name='contest',
        version='0.0.1',
        author="Javier Segovia-Aguas and Vicenç Gómez",
        packages=find_packages('src'),
        package_dir={'': 'src'},
        setup_requires=['wheel'],
    )

if __name__ == "__main__":
    main()
