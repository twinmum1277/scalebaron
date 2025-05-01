from setuptools import setup

setup(
    name='scalebaron',
    version='1.0.0',
    description='ScaleBarOn: A Python Tool for Scaling Multiple Elemental Maps',
    author='Tracy Punshon',
    author_email='tracy.punshon@dartmouth.edu',
    license='MIT',
    py_modules=['scalebaron'],
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'Pillow',
        'openpyxl',
        'scipy'
    ],
    entry_points={
        'console_scripts': [
            'scalebaron = scalebaron:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
