import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import sdist_upip

setup(name='micropython-mqttse',
      version='1.1',
      description='Lightweight mqttse library for MicroPython, nonblocking Mqtt for ESP8266.',
      long_description=open('README.rst').read(),
      url='https://github.com/straga/micropython/tree/master/projects/modules_my/MqttSe',
      author='https://github.com/straga',
      author_email='vostraga@gmail.com',
      maintainer='micropython-lib Developers',
      maintainer_email='vostraga@gmail.com',
      license='MIT',
      cmdclass={'sdist': sdist_upip.sdist},
      packages=['mqttse'],
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: Implementation :: MicroPython',
    ],
)
