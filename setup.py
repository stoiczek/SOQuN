import os

from setuptools import setup, find_packages
import soqun

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()
SCRIPT_PREFIX = 'soqun_'
requires = [
    'requests',              # For SA API
    'python-simple-hipchat', # For hipchat notifications
    'Jinja2'                 # For message formatting
]

def _get_console_scripts():
    import os.path

    cmd_scripts_dir = os.path.join(os.path.dirname(soqun.__file__), 'cmd_scripts')

    scripts_string = []
    for file_name in os.listdir(cmd_scripts_dir):
        if file_name.endswith('.py') and not file_name.startswith('_'):
            mod_name = os.path.basename(file_name)
            mod_name = mod_name[0:len(mod_name) - 3]
            scripts_string.append(SCRIPT_PREFIX + mod_name +
                                  ' = soqun.cmd_scripts.' + mod_name + ':main\n')
    return ''.join(scripts_string)

print _get_console_scripts()

def _get_entry_points():
    return "[console_scripts]\n{0}".format(_get_console_scripts())


setup(name='soqun',
      version='0.0',
      description='SOQuN - StackOverflow Query Notifier',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",

          ],
      author='Tadusz Kozak',
      author_email='ted@addlive.com',
      url='',
      keywords='stackoverflow requests hipchat',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='soqun',
      install_requires=requires,
      entry_points=_get_entry_points(),
      )

