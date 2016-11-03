import os
import time
import yaml

import utils._yaml
import core.outputstorage
import services.base
import services.exception


class Company(services.base.Service):
    """
        >>> import shutil
        >>> import services.company
        >>> import interface.gitinterface
        >>> repo_name = 'services/test_repo'
        >>> interface = interface.gitinterface.GitInterface(repo_name)
        >>> svc_co = services.company.Company(interface.path)
        >>> svc_co.add('CompanyA', 'This is Co.A', 'Dever')
        True
        >>> co = svc_co.getyaml('CompanyA')
        >>> co['name']
        'CompanyA'
        >>> co['introduction']
        'This is Co.A'
        >>> svc_co.add('CompanyA', 'This is Co.A', 'Dever') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ExistsCompany: CompanyA
        >>> svc_co.names()
        ['CompanyA']
        >>> svc_co.getyaml('CompanyB') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        NotExistsCompany
        >>> shutil.rmtree(repo_name)
    """
    CO_DIR = 'CO'

    def __init__(self, path, name=None):
        self.path = os.path.join(path, self.CO_DIR)
        super(Company, self).__init__(self.path, name)
        self._nums = 0

    def exists(self, id):
        yamlname = core.outputstorage.ConvertName(id).yaml
        result = self.interface.exists(yamlname)
        return result

    def add(self, coobj, committer=None, unique=True, yamlfile=True):
        if unique is True and self.exists(coobj.name):
            raise services.exception.ExistsCompany(coobj.name)
        name = core.outputstorage.ConvertName(coobj.name)
        message = "Add company: %s data." % name
        self.interface.add(name.md, coobj.data, message=message, committer=committer)
        if yamlfile is True:
            coobj.metadata['committer'] = committer
            coobj.metadata['date'] = time.time()
            message = "Add company: %s metadata." % name
            self.interface.add(name.yaml, yaml.safe_dump(coobj.metadata, allow_unicode=True),
                               message=message, committer=committer)
        self._nums += 1
        return True

    def getmd(self, name):
        result = unicode()
        md = core.outputstorage.ConvertName(name).md
        markdown = self.interface.get(md)
        if markdown is None:
            result = None
        elif isinstance(markdown, unicode):
            result = markdown
        else:
            result = unicode(str(markdown), 'utf-8')
        return result

    def getyaml(self, id):
        name = core.outputstorage.ConvertName(id).yaml
        yaml_str = self.interface.get(name)
        if yaml_str is None:
            raise IOError
        return yaml.load(yaml_str, Loader=utils._yaml.SafeLoader)

    def yamls(self):
        yamls = self.interface.lsfiles('.', '*.yaml')
        for each in yamls:
            yield os.path.split(each)[-1]

    def names(self):
        for each in self.yamls():
            yield core.outputstorage.ConvertName(each)

    def datas(self):
        for name in self.names():
            text = self.getmd(name)
            yield name, text

    @property
    def NUMS(self):
        if not self._nums:
            self._nums = len(list(self.yamls()))
        return self._nums
