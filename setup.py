from setuptools import setup, find_packages

setup(name='peitho',
	version='0.1',
	description='Perfecting Experiments with Information Theory',
	url='https://github.com/ld2113/Experimental-Design',
	author='Leander Dony, Scott Ward, Jonas Mackerodt',
	author_email='jonas.mackerodt16@imperial.ac.uk',
	license='MIT',
	packages=find_packages(),
	include_package_data=True,
	install_requires = [
		'pycuda',
		'numpy',
		'matplotlib',
		'python-libsbml'
	],
	entry_points = {
		'console_scripts': ['peitho=peitho.main.main:main']
		},
	zip_safe=False)
