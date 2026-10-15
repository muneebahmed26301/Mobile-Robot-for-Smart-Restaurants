from setuptools import find_packages, setup
from glob import glob

package_name = 'camera_line_follow'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='raze',
    maintainer_email='zakmalik9@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'clf_node = camera_line_follow.clf_node:main',
            'image_processor = camera_line_follow.image_processor:main',
            'junction_classifier = camera_line_follow.junction_classifier:main',
            'error_calculator = camera_line_follow.error_calculator:main',
        ],
    },
)
