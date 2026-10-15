from setuptools import find_packages, setup
from glob import glob

package_name = 'master_controller'

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
    maintainer='zakriya',
    maintainer_email='zakriya@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'master_node = master_controller.master_node:main',
            'line_mapper = master_controller.line_mapper:main',
            'line_planner = master_controller.line_planner:main',
            'motor_controller = master_controller.motor_controller:main',
            'iot_core = master_controller.iot_core:main',
        ],
    },
)
