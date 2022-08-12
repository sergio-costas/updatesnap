#!/usr/bin/env python3

import requests
import sys
import yaml
import urllib
import re
import time
import os
import datetime

class Colors(object):
    def __init__(self):
        self.red = "\033[31m"
        self.green = "\033[32m"
        self.yellow = "\033[33m"
        self.cyan = "\033[36m"
        self.reset = "\033[0m"

        self.critical = self.red
        self.warning = self.yellow
        self.ok = self.green
        self.note = self.cyan


    def clear_line(self):
        print("\033[2K", end="\r") # clear the line


class Version(object):
    def __init__(self, version_string):
        self.major = None
        self.minor = None
        self.revision = None
        self.rc = None
        self.valid = False

        if version_string.startswith("wip/"):
            return

        # MAJOR.MINOR.REVISION.RC
        if self._check_majorminorrevision(version_string, '.', False, rcseparator='.'):
            return

        # MAJOR.MINOR.REVISION
        if self._check_majorminorrevision(version_string, '.', False):
            return

        # MAJOR.MINOR.REVISIONrcXX
        if self._check_majorminorrevision(version_string, '.', False, rcseparator='rc'):
            return

        # MAJOR.MINOR.REVISION.rcXX
        if self._check_majorminorrevision(version_string, '.', False, rcseparator='.rc'):
            return

        # MAJOR.MINOR.REVISION-XX
        if self._check_majorminorrevision(version_string, '.', False, rcseparator='-'):
            return

        # aaaaMAJOR.MINOR.REVISION
        if self._check_majorminorrevision(version_string, '.', True):
            return

        # aaaaMAJOR_MINOR_REVISION
        if self._check_majorminorrevision(version_string, '_', True):
            return

        # aaaaMAJOR-MINOR-REVISION
        if self._check_majorminorrevision(version_string, '-', True):
            return

        # MAJOR.MINOR
        if self._check_majorminor(version_string, '.', False):
            return


        # MAJOR-MINOR
        if self._check_majorminor(version_string, '-', False):
            return

        # MAJOR_MINOR
        if self._check_majorminor(version_string, '_', False):
            return

        # aaaaMAJOR.MINOR
        if self._check_majorminor(version_string, '.', True):
            return

        # aaaaMAJOR-MINOR
        if self._check_majorminor(version_string, '-', True):
            return

        # aaaaMAJOR_MINOR
        if self._check_majorminor(version_string, '_', True):
            return

        # MAJOR
        if self._check_major(version_string, False):
            return

        # aaaaMAJOR
        if self._check_major(version_string, True):
            return

        # MAJOR.MINORaaaa
        if self._check_majorminor(version_string, '.', False, True):
            return


    def _check_major(self, version_string, prefix):
        search_string = f'[0-9]+$'
        if not prefix:
            search_string = '^' + search_string
        s = re.search(search_string, version_string)
        if s:
            s = s.group()
            self.major = int(s)
            self.valid = True
            return True
        return False


    def _check_majorminor(self, version_string, separator, prefix, suffix = False):
        separator2 = separator.replace('.', '[.]')
        search_string = f'[0-9]+{separator2}[0-9]+'
        if not suffix:
            search_string += '$'
        if not prefix:
            search_string = '^' + search_string
        s = re.search(search_string, version_string)
        if s:
            s = s.group()
            n = s.split(separator)
            self.major = int(n[0])
            self.minor = int(n[1])
            self.valid = True
            return True
        return False


    def _check_majorminorrevision(self, version_string, separator, prefix, rcseparator = None, suffix = False):
        if rcseparator:
            rcseparator2 = rcseparator.replace('.', '[.]')
        separator2 = separator.replace('.', '[.]')
        search_string = f'[0-9]+{separator2}[0-9]+{separator2}[0-9]+'
        if not prefix:
            search_string = '^' + search_string
        if rcseparator:
            search_string += f'{rcseparator2}[0-9]+'
        if not suffix:
            search_string += '$'
        s = re.search(search_string, version_string)
        if s:
            s = s.group()
            if rcseparator:
                rcsepos = s.rfind(rcseparator)
                self.rc = int(s[rcsepos + len(rcseparator):])
                s = s[:rcsepos]
            n = s.split(separator)
            self.major = int(n[0])
            self.minor = int(n[1])
            self.revision = int(n[2])
            self.valid = True
            return True
        return False


    def __str__(self):
        if self.major is None:
            return "Unknown"
        version = str(self.major)
        if self.minor is None:
            return version
        version += "." + str(self.minor)
        if self.revision is None and self.rc is None:
            return version
        if self.revision is not None:
            version += "." + str(self.revision)
        if self.rc is not None:
            version += "rc" + str(self.rc)
        return version


    def __repr__(self):
        return self.__str__()


    def is_newer(self, other, also_equal = False):
        if not self.valid:
            return False
        if not other.valid:
            return True
        if self.major is None and other.major is None:
            return also_equal
        if self.major is None:
            return False
        if other.major is None:
            return True
        if self.major > other.major:
            return True
        if self.major < other.major:
            return False

        if self.minor is None and other.minor is None:
            return also_equal
        if self.minor is None:
            return False
        if other.minor is None:
            return True
        if self.minor > other.minor:
            return True
        if self.minor < other.minor:
            return False

        # It is possible to have major.minor RC
        if self.revision is not None or other.revision is not None:
            if self.revision is None:
                return False
            if other.revision is None:
                return True
            if self.revision > other.revision:
                return True
            if self.revision < other.revision:
                return False

        if self.rc is None and other.rc is None:
            return also_equal
        if self.rc is None:
            return False
        if other.rc is None:
            return True
        if self.rc > other.rc:
            return True
        if self.rc < other.rc:
            return False

        return also_equal


class GitClass(object):
    def __init__(self, repo_type, secrets):
        super().__init__()
        self._token = None
        self._user = None
        self._colors = Colors()
        if (repo_type == 'github') and 'github' in secrets:
            self._user = secrets['github']['user']
            self._token = secrets['github']['token']


    def _read_uri(self, uri):
        print(f"Asking URI {uri}     ", end="\r")
        while True:
            try:
                if (self._user is not None) and (self._token is not None):
                    response = requests.get(uri, auth=requests.auth.HTTPBasicAuth(self._user, self._token))
                else:
                    response = requests.get(uri)
                break
            except:
                print(f"Retrying URI {uri}     ", end="\r")
                time.sleep(1)
        return response


    def _read_pages(self, uri):
        elements = []
        while uri is not None:
            response = self._read_uri(uri)
            if response.status_code != 200:
                print(f"{self._colors.critical}Status code {response.status_code} when asking for {uri}{self._colors.reset}")
                return []
            headers = response.headers
            data = response.json()
            for entry in data:
                elements.append(entry)
            uri = None
            if "Link" in headers:
                l = headers["link"]
                entries = l.split(",")
                for e in entries:
                    if 'rel="next"' not in e:
                        continue
                    p1 = e.find("<")
                    p2 = e.find(">")
                    uri = e[p1+1:p2]
                    break
        self._colors.clear_line()
        return elements


    def _read_page(self, uri):
        response = self._read_uri(uri)
        if response.status_code != 200:
            print(f"{self._colors.critical}Status code {response.status_code} when asking for {uri}{self._colors.reset}")
            return None
        headers = response.headers
        data = response.json()
        return data


    def _get_uri(self, repository, min_elements):
        repository = repository.strip()
        if repository[-4:] == '.git':
            repository = repository[:-4]
        uri = urllib.parse.urlparse(repository)
        elements = uri.path.split("/")
        if (uri.scheme != 'http') and (uri.scheme != 'https') and (uri.scheme != 'git'):
            print(f"{self._colors.critical}Unrecognized protocol in repository {repository}{self._colors.reset}")
            return None
        elements = uri.path.split("/")
        if len(elements) < min_elements:
            print(f"{self._colors.critical}Invalid uri format for repository {repository}{self._colors.reset}")
            return None
        return uri


    def _rb(self, text):
        """ Remove trailing and heading '/' characters, to simplify building URIs """
        while (len(text) > 0) and (text[0] == '/'):
            text = text[1:]
        while (len(text) > 0) and (text[-1] == '/'):
            text = text[:-1]
        return text


    def join_url(self, *args):
        if len(args) == 0:
            return ""
        output = args[0]
        for element in args[1:]:
            if output[-1] == '/':
                output = output[:-1]
            if element[0] == '/':
                element = element[1:]
            output += '/' + element
        return output


class Github(GitClass):
    def __init__(self, secrets):
        super().__init__("github", secrets)
        self._api_url = 'https://api.github.com/repos/'


    def _is_github(self, repository):
        uri = self._get_uri(repository, 3)
        if uri is None:
            return None
        if (uri.netloc != "github.com") and (uri.netloc != "www.github.com"):
            return None
        return uri


    def get_branches(self, repository):
        uri = self._is_github(repository)
        if uri is None:
            return None

        branch_command = self.join_url(self._api_url, uri.path, 'branches')
        return self._read_pages(branch_command)


    def get_tags(self, repository):
        uri = self._is_github(repository)
        if uri is None:
            return None

        tag_command = self.join_url(self._rb(self._api_url), self._rb(uri.path), 'tags')
        data = self._read_pages(tag_command)
        tags = []
        for tag in data:
            tag_info = self._read_page(tag['commit']['url'])
            if tag_info is None:
                continue
            if 'commiter' in tag_info['commit']:
                date = tag_info['commit']['committer']['date']
            else:
                date = tag_info['commit']['author']['date']
            tags.append({"name": tag['name'],
                         "date": datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")})
        self._colors.clear_line()
        return tags



class Gitlab(GitClass):
    def __init__(self, secrets):
        super().__init__("gitlab", secrets)


    def _is_gitlab(self, repository):
        uri = self._get_uri(repository, 3)
        if uri is None:
            return None
        if "gitlab" not in uri.netloc:
            return None
        return uri


    def _project_name(self, uri):
        name = uri.path
        while name[0] == '/':
            name = name[1:]
        return name.replace('/', '%2F')


    def get_branches(self, repository):
        uri = self._is_gitlab(repository)
        if uri is None:
            return None

        branch_command = self.join_url(uri.scheme + '://', uri.netloc, 'api/v4/projects', self._project_name(uri), 'repository/branches')
        data = self._read_pages(branch_command)
        branches = []
        for branch in data:
            branches.append({"name": branch['name']})
        return branches


    def get_tags(self, repository):
        uri = self._is_gitlab(repository)
        if uri is None:
            return None

        tag_command = self.join_url(uri.scheme + '://', uri.netloc, 'api/v4/projects', self._project_name(uri), 'repository/tags')
        data = self._read_pages(tag_command)
        tags = []
        for tag in data:
            tags.append({"name": tag['name'],
                         "date": datetime.datetime.fromisoformat(tag['commit']['committed_date'])})
        self._colors.clear_line()
        return tags


class Snapcraft(object):
    def __init__(self, filename = None):
        super().__init__()
        self._colors = Colors()
        if filename is None:
            filename = '.'
        if os.path.isdir(filename):
            f1 = os.path.join(filename, "snapcraft.yaml")
            if not os.path.exists(f1):
                f1 = os.path.join(filename, "snap", "snapcraft.yaml")
                if not os.path.exists(f1):
                    print(f"No snapcraft file found at folder {filename}")
            filename = f1
        if os.path.exists(filename):
            print(f"Opening file {filename}")
            with open(filename, "r") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = None
        self._load_secrets(filename)
        self._github = Github(self._secrets)
        self._gitlab = Gitlab(self._secrets)
        self.get_versions = True
        self._last_part = None


    def _load_secrets(self, filename):
        secrets_file = os.path.expanduser('~/.config/updatesnap/updatesnap.secrets')
        if os.path.exists(secrets_file):
            with open(secrets_file, "r") as cfg:
                self._secrets = yaml.safe_load(cfg)
            return
        secrets_file = os.path.join(os.path.split(os.path.abspath(filename))[0], "updatesnap.secrets")
        if os.path.exists(secrets_file):
            with open(secrets_file, "r") as cfg:
                self._secrets = yaml.safe_load(cfg)
            return
        self._secrets = {}


    def _print_message(self, part, message, source = None):
        if part != self._last_part:
            print(f"Part: {self._colors.note}{part}{self._colors.reset}{f' ({source})' if source else ''}")
            self._last_part = part
        if message is not None:
            print("  " + message, end="")
            print(self._colors.reset)


    def _get_tags(self, source):
        if not self.get_versions:
            return []
        tags = self._github.get_tags(source)
        if tags is not None:
            return tags
        tags = self._gitlab.get_tags(source)
        return tags


    def _get_branches(self, source):
        if not self.get_versions:
            return []
        branches = self._github.get_branches(source)
        if branches is not None:
            return branches
        branches = self._gitlab.get_branches(source)
        return branches


    def _get_version(self, entry, check = False):

        version = Version(entry)
        if (not version.valid) and check:
            print(f"{self._colors.critical}Unknown tag/branch format for {entry}{self._colors.reset}")
        return version


    def process_parts(self):
        if self._config is None:
            return
        for part in self._config['parts']:
            self.process_part(part)


    def process_part(self, part):
            data = self._config['parts'][part]
            if 'source' not in data:
                return
            source = data['source']

            if ((not source.startswith('http://')) and
                (not source.startswith('https://')) and
                (not source.startswith('git://')) and
                ((not 'source-type' in data) or (data['source-type'] != 'git'))):
                    self._print_message(part, f"{self._colors.critical}Source is neither http:// nor git://{self._colors.reset}", source = source)
                    print()
                    return

            if (not source.endswith('.git')) and ((not 'source-type' in data) or (data['source-type'] != 'git')):
                self._print_message(part, f"{self._colors.warning}Source is not a GIT repository{self._colors.reset}", source = source)
                print()
                return

            if 'savannah' in source:
                url = urllib.parse.urlparse(source)
                if 'savannah' in url.netloc:
                    self._print_message(part, f"{self._colors.warning}Savannah repositories not supported{self._colors.reset}", source = source)
                    print()
                    return

            self._print_message(part, None, source = source)
            tags = self._get_tags(source)

            if ('source-tag' not in data) and ('source-branch' not in data):
                self._print_message(part, f"{self._colors.warning}Has neither a source-tag nor a source-branch{self._colors.reset}", source = source)
                self._print_last_tags(part, tags)

            if 'source-tag' in data:
                self._print_message(part, f"Current tag: {data['source-tag']}", source = source)
                current_version = self._get_version(data['source-tag'], True)
                self._sort_tags(part, data['source-tag'], tags)

            if 'source-branch' in data:
                self._print_message(part, f"Current branch: {data['source-branch']}", source = source)
                current_version = self._get_version(data['source-branch'], True)
                self._print_message(part, f"Current version: {current_version}")
                branches = self._get_branches(source)
                self._sort_elements(part, current_version, branches, "branch")
                self._print_message(part, f"{self._colors.note}Should be moved to an specific tag{self._colors.reset}")
                self._print_last_tags(part, tags)
            print()


    def _print_last_tags(self, part, tags):
        tags.sort(reverse = True, key=lambda x: x.get('date'))
        tags = tags[:4]
        self._print_message(part, f"Last tags:")
        for tag in tags:
            self._print_message(part, f"  {tag['name']} ({tag['date']})")


    def _sort_tags(self, part, current_tag, tags):
        if tags is None:
            self._print_message(part, f"{self._colors.critical}No tags found")
            return
        current_date = None
        for tag in tags:
            if tag['name'] == current_tag:
                current_date = tag['date']
                break
        if current_date is None:
            self._print_message(part, f"{self._colors.critical}Error:{self._colors.reset} can't find the current tag in the tag list.")
            return
        self._print_message(part, f"Current tag date: {current_date}")
        newer_tags = [t for t in tags if (t['date'] >= current_date) and (t['name'] != current_tag)]
        if len(newer_tags) == 0:
            self._print_message(part, f"{self._colors.ok}Tag updated{self._colors.reset}")
        else:
            self._print_message(part, f"{self._colors.warning}Newer tags:{self._colors.reset}")
            newer_tags.sort(reverse = True, key=lambda x: x.get('date'))
            for tag in newer_tags:
                self._print_message(part, f"  {tag['name']} ({tag['date']})")

    def _sort_elements(self, part, current_version, elements, text, show_equal = False):
        newer_elements = []
        if elements is None:
            elements = []
        for element in elements:
            if (current_version is None) or self._get_version(element['name']).is_newer(current_version, show_equal):
                newer_elements.append(element['name'])
        if len(newer_elements) == 0:
            self._print_message(part, f"{self._colors.ok}Branch updated{self._colors.reset}")
        else:
            self._print_message(part, text)
            newer_elements.sort(reverse = True)
            for element in newer_elements:
                self._print_message(part, "  " + element)


if sys.argv[1] == '-s':
    silent = True
    sys.argv = [sys.argv[0]] + sys.argv[2:]
else:
    silent = False



snap = Snapcraft(sys.argv[1])
if silent:
    snap.get_versions = False
if len(sys.argv) > 2:
    for a in sys.argv[2:]:
        snap.process_part(a)
else:
    snap.process_parts()
