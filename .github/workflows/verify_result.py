# -*- coding: utf-8 -*-
from pathlib import Path
import os
import os.path
import ssl
import sys
import getopt
import json
import shutil
import re
import requests

def prepare_config_file(sample_filename, filename, arguments):
    """
    Prepares a configuration file based on a sample file and a set of arguments.

    This function performs the following steps:
    1. Checks if the sample file exists. If not, it returns False.
    2. If the target file already exists, it removes it.
    3. Copies the sample file to the target file location.
    4. Opens the new file and reads its contents.
    5. Iterates over each line in the file and each argument in the arguments list.
    6. For each argument, it finds the name and value and constructs a new line with these values.
    7. Writes the modified lines back to the file.
    8. Prints the contents of the new file for debugging purposes.

    Args:
        sample_filename (str): The path to the sample configuration file.
        filename (str): The path where the new configuration file should be created.
        arguments (list): A list of strings where each string is
          an argument in the format 'name=value'.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """

    if not os.path.exists(sample_filename):
        print('no sample file exist')
        return False

    if os.path.exists(filename):
        print(filename + ' file already exist, removing it')
        os.remove(filename)

    shutil.copyfile(sample_filename, filename)

    if not os.path.exists(filename):
        print('no file exist')
        return False

    with open(filename, 'r', encoding="utf-8") as file:
        data = file.readlines()
        output = list('')
        for line in data:
            tmp = line
            for argument in arguments:
                index = argument.find('=')
                name = argument[:index]
                value = argument[(index + 1):]

                regex_argument = f'^{name}.*'
                if value in ('True', 'False', 'None'):
                    result_argument = f'{name} = {value}'
                else:
                    result_argument = f"{name} = '{value}'"


                tmp = re.sub(regex_argument, result_argument,
                             tmp, 0, re.MULTILINE)
            output.append(tmp)

    with open(filename, 'w', encoding="utf-8") as outfile:
        outfile.writelines(output)

    # show resulting config in output for debug reasons
    print('config.py:\n')
    print('\n'.join(output))
    return True


def make_test_comparable(input_filename):
    """
    Modifies a JSON test file to make it comparable by removing date information.

    This function performs the following steps:
    1. Opens the input file and loads the JSON data.
    2. Iterates over each test in the data. If a test contains a "date" field,
      it replaces the date with the string "removed for comparison".
    3. Writes the modified data back to the input file.

    Args:
        input_filename (str): The path to the JSON file to be modified.

    Note: This function modifies the input file in-place.
      Make sure to create a backup if you need to preserve the original data.
    """

    with open(input_filename, encoding="utf-8") as json_input_file:
        data = json.load(json_input_file)
        for test in data["tests"]:
            if "date" in test:
                test["date"] = "removed for comparison"

    with open(input_filename, 'w', encoding="utf-8") as outfile:
        json.dump(data, outfile)


def print_file_content(input_filename):
    """
    Prints the content of a file line by line.

    This function performs the following steps:
    1. Prints the name of the input file.
    2. Opens the input file in read mode.
    3. Reads the file line by line.
    4. Prints each line.

    Args:
        input_filename (str): The path to the file to be read.

    Note: This function assumes that the file exists and can be opened.
      If the file does not exist or cannot be opened, an error will occur.
    """

    print('input_filename=' + input_filename)
    with open(input_filename, 'r', encoding="utf-8") as file:
        data = file.readlines()
        for line in data:
            print(line)


def get_file_content(input_filename):
    """
    Reads the content of a file and returns it as a string.

    This function performs the following steps:
    1. Opens the input file in read mode.
    2. Reads the file line by line and stores each line in a list.
    3. Joins the list of lines into a single string with newline characters between each line.

    Args:
        input_filename (str): The path to the file to be read.

    Returns:
        str: The content of the file as a string.

    Note: This function assumes that the file exists and can be opened.
      If the file does not exist or cannot be opened, an error will occur.
    """

    with open(input_filename, 'r', encoding='utf-8') as file:
        lines = []
        data = file.readlines()
        for line in data:
            lines.append(line)
    return '\n'.join(lines)

def validate_failures():
    """
    Verifies if a unhandled exception occured or not.
    If True, we print content of failures.log
    If False, we do nothing
    """
    base_directory = Path(os.path.dirname(
            os.path.realpath(__file__)) + os.path.sep).parent.parent
    filename = 'failures.log'
    filename = os.path.join(base_directory.resolve(), filename)
    if not os.path.exists(filename):
        print(f'no {filename} exists')
        return True

    print('failures happend while running test')
    print_file_content(filename)
    return True

def validate_testresult(arg): # pylint: disable=too-many-return-statements,too-many-branches,too-many-statements
    """
    Validates the test result by checking the existence and content of a specific JSON file.

    This function checks if a JSON file named 'testresult-{test_id}.json' exists
      in the same directory as this script.
    If the file exists, it checks if it has a valid test content.

    Parameters:
    arg (str): The test_id used to identify the test result file.

    Returns:
    bool: True if the test result file exists and contains valid test results, False otherwise.
    """

    base_directory = os.path.dirname(os.path.realpath(__file__)) + os.path.sep
    test_id = arg
    filename = f'testresult-{test_id}.json'
    filename = os.path.join(base_directory, filename)
    if not os.path.exists(filename):
        print('test result doesn\'t exists')
        return False

    content = get_file_content(filename)
    # for all other test it is enough that we have a file in place for now
    if '{"tests": []}' in content:
        print('Test failed, empty test results only')
        print_file_content(filename)
        return False

    data = json.loads(content)
    if not isinstance(data, dict):
        print('Test failed, test results are not a dict')
        print_file_content(filename)
        return False

    if 'tests' not in data:
        print('Test failed, test results doesn\'t have a root element \'tests\'')
        print_file_content(filename)
        return False

    if not isinstance(data['tests'], list):
        print('Test failed, test results are not in a list under the \'tests\' element')
        print_file_content(filename)
        return False

    if len(data['tests']) == 0:
        print('Test failed, has less than 1 test results')
        print_file_content(filename)
        return False

    first_test_result = data['tests'][0]
    if 'site_id' not in first_test_result:
        print('Test failed, missing \'site_id\' field in first test result')
        print_file_content(filename)
        return False

    if 'type_of_test' not in first_test_result:
        print('Test failed, missing \'type_of_test\' field in first test result')
        print_file_content(filename)
        return False

    if 'report' not in first_test_result:
        print('Test failed, missing \'report\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_sec' not in first_test_result:
        print('Test failed, missing \'report_sec\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_perf' not in first_test_result:
        print('Test failed, missing \'report_perf\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_a11y' not in first_test_result:
        print('Test failed, missing \'report_a11y\' field in first test result')
        print_file_content(filename)
        return False

    if 'report_stand' not in first_test_result:
        print('Test failed, missing \'report_stand\' field in first test result')
        print_file_content(filename)
        return False

    if 'date' not in first_test_result:
        print('Test failed, missing \'date\' field in first test result')
        print_file_content(filename)
        return False

    if 'data' not in first_test_result:
        print('Test failed, missing \'data\' field in first test result')
        print_file_content(filename)
        return False

    if int(test_id) != first_test_result['type_of_test']:
        print('Test failed, \'type_of_test\' field is using wrong test id')
        print_file_content(filename)
        return False

    if 'rating' not in first_test_result or\
            'rating_sec' not in first_test_result or\
            'rating_perf' not in first_test_result or\
            'rating_a11y' not in first_test_result or\
            'rating_stand' not in first_test_result:
        print('Test failed, missing one or more rating field(s) in first test result')
        print_file_content(filename)
        return False

    highest_rating = -1.0
    highest_rating = max(first_test_result['rating'], highest_rating)
    highest_rating = max(first_test_result['rating_sec'], highest_rating)
    highest_rating = max(first_test_result['rating_perf'], highest_rating)
    highest_rating = max(first_test_result['rating_a11y'], highest_rating)
    highest_rating = max(first_test_result['rating_stand'], highest_rating)

    if highest_rating == -1.0:
        print('Test failed, no rating was set during the test')
        print_file_content(filename)
        return False

    print('test result exists')
    print_file_content(filename)
    return True

def get_content(url, allow_redirects=False, use_text_instead_of_content=True):
    """Trying to fetch the response content
    Attributes: url, as for the URL to fetch
    """

    try:
        headers = {
            'user-agent': (
                'Mozilla/5.0 (compatible; Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 '
                'Safari/537.36 Edg/88.0.705.56'
            )
        }

        a = requests.get(url, allow_redirects=allow_redirects,
                         headers=headers, timeout=120)

        if use_text_instead_of_content:
            content = a.text
        else:
            content = a.content
        return content
    except ssl.CertificateError as error:
        print(f'Info: Certificate error. {error.reason}')
    except requests.exceptions.SSLError as error:
        if 'http://' in url:  # trying the same URL over SSL/TLS
            print('Info: Trying SSL before giving up.')
            return get_content(url.replace('http://', 'https://'))
        print(f'Info: SSLError. {error}')
        return ''
    except requests.exceptions.ConnectionError as error:
        if 'http://' in url:  # trying the same URL over SSL/TLS
            print('Connection error! Info: Trying SSL before giving up.')
            return get_content(url.replace('http://', 'https://'))
        print(
            f'Connection error! Unfortunately the request for URL "{url}" failed.'
            f'\nMessage:\n{sys.exc_info()[0]}')
        return ''
    except requests.exceptions.Timeout:
        print(
            f'Timeout error! Unfortunately the request for URL "{url}" timed out. '
            f'The timeout is set to {120} seconds.\n'
            f'Message:\n{sys.exc_info()[0]}')
    except requests.exceptions.RequestException as error:
        print(
            f'Error! Unfortunately the request for URL "{url}" failed for other reason(s).\n'
            f'Message:\n{error}')
    return ''

def set_file(file_path, content, use_text_instead_of_content):
    """
    Writes the provided content to a file at the specified path.

    If 'use_text_instead_of_content' is True,
        the function opens the file in text mode and writes the content as a string.
    If 'use_text_instead_of_content' is False,
        the function opens the file in binary mode and writes the content as bytes.

    Args:
        file_path (str): The path to the file where the content will be written.
        content (str or bytes): The content to be written to the file.
        use_text_instead_of_content (bool): 
            Determines whether the file is opened in text or binary mode.

    Returns:
        None
    """
    if use_text_instead_of_content:
        with open(file_path, 'w', encoding='utf-8', newline='') as file:
            file.write(content)
    else:
        with open(file_path, 'wb') as file:
            file.write(content)

def main(argv):
    """
    WebPerf Core - Regression Test

    Usage:
    verify_result.py -h

    Options and arguments:
    -h/--help\t\t\t: Verify Help command
    -l/--language\t\t: Verify languages
    -c/--prep-config <activate feature, True or False>\t\t:
      Uses SAMPLE-config.py to creat config.py
    -t/--test <test number>\t: Verify result of specific test

    NOTE:
    If you get this in step "Setup config [...]" you forgot to
    add repository secret for your repository.
    More info can be found here: https://github.com/Webperf-se/webperf_core/issues/81
    """

    try:
        opts, _ = getopt.getopt(argv, "hlc:t:", [
                                   "help", "test=", "prep-config=", "language"])
    except getopt.GetoptError:
        print(main.__doc__)
        sys.exit(2)

    if len(opts) == 0:
        print(main.__doc__)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):  # help
            print(main.__doc__)
            sys.exit(0)
        elif opt in ("-c", "--prep-config"):
            handle_pre_config(arg)
        elif opt in ("-t", "--test"):  # test id
            handle_test_result(arg)

    # No match for command so return error code to fail verification
    sys.exit(2)

def handle_test_result(arg):
    """ Terminate the programme with an error if our test contains unexpected content  """
    if not validate_failures():
        sys.exit(2)

    if validate_testresult(arg):
        sys.exit(0)
    else:
        sys.exit(2)

def handle_pre_config(arg):
    """ Terminate the programme with an error if we're unable to
      generate a config.py file from SAMPLE-config with a few alterations """
    if 'true' == arg.lower() or 'false' == arg.lower() or '1' == arg or '0' == arg:
        raise ValueError(
                    'c/prep-config argument has changed format,'
                    ' it doesn\'t support previous format')
    arguments = arg.split(',')

    if prepare_config_file('SAMPLE-config.py', 'config.py', arguments):
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1:])
