from setuptools import setup, find_packages

setup(
    name='cbct',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pydicom',
        'numpy',
        'nibabel',
        'scipy',
        'Pillow',
        'imageio',
    ],
    entry_points={
        'console_scripts': [
            'cbct = scripts.main:main',
        ],
    },
)
