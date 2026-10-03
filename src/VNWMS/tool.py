import os
import shutil
import subprocess
import sys
from django.db import connection

'''
proposal :  

init : set your project DJANGO_SETTINGS_MODULE before executing this program

command : python tool.py cleanmigrations
1. delete all files and directions except __init__.py under migrations folder
2. delete all django_migrations content
3. execute shell makemigrations and migrate --fake-initial

command : python tool.py cleanmigrations app_name
the same as the above commands with the specific app_name

'''

DJANGO_SETTINGS_MODULE = "VNWMS.settings.test-box-local"

class ManagementUtility(object):
    """
    Encapsulates the logic of the django-admin and manage.py utilities.
    """
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        self.settings_exception = None

    def execute(self):
        """
        Given the command-line arguments, this figures out which subcommand is
        being run, creates a parser appropriate to that command, and runs it.
        """
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = 'help'  # Display help if no arguments were given.

        if subcommand == 'cleanmigrations':
            try:
                app_name = self.argv[2]
            except IndexError:
                app_name = None

            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            MIGRATIONS_ROOT = os.path.join(BASE_DIR, 'migrations/')

            if app_name:
                print("=====Delete files are starting=====")
                app_dir = os.path.join(MIGRATIONS_ROOT, app_name)
                rmdircontent(app_dir)
                print("=====Delete files done=====")

                print("=====DB start connect=====")
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)
                cursor = connection.cursor()
                cursor.execute("delete from django_migrations where app='{app}';".format(app=app_name))
                print("=====DB clean done=====")

                print("=====Makemigrations start=====")
                output = subprocess.check_output(["python", "manage.py", "makemigrations", app_name])
                for line in str(output).split('\\r\\n'):
                    print(line)

                output = subprocess.check_output(["python", "manage.py", "migrate", "--fake-initial"])
                for line in str(output).split('\\r\\n'):
                    print(line)
                print("=====migrate done=====")
            else:
                for app_name in os.listdir(MIGRATIONS_ROOT):
                    print("=====Delete files are starting=====")
                    app_dir = os.path.join(MIGRATIONS_ROOT, app_name)
                    rmdircontent(app_dir)
                    print("=====Delete files done=====")

                print("=====DB start connect=====")
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)
                cursor = connection.cursor()
                cursor.execute("delete from django_migrations;")
                print("=====DB clean done=====")

                print("=====Makemigrations start=====")
                output = subprocess.check_output(["python", "manage.py", "makemigrations"])
                for line in str(output).split('\\r\\n'):
                    print(line)

                output = subprocess.check_output(["python", "manage.py", "migrate", "--fake-initial"])
                for line in str(output).split('\\r\\n'):
                    print(line)
                print("=====migrate done=====")


def rmdircontent(app_dir):
    print("Path:" + app_dir)
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            if file != '__init__.py':
                os.remove(os.path.join(root, file))
                print("Delete file:" + file)
        for dir in dirs:
            shutil.rmtree(os.path.join(root, dir))
            print("Delete dir:" + dir)


def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    utility = ManagementUtility(argv)
    utility.execute()


if __name__ == '__main__':
    execute_from_command_line(sys.argv)




