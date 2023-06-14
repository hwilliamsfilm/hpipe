from core.hutils import path
from core.hutils import logger
import re
from core.hutils import errors
import os


class ProjectFile:
    """
    The base class for all project files on the server.
    """

    def __init__(self, filepath):
        self.filepath = path.fix_path(filepath)

    def __repr__(self):
        return '<Project File {name}>'.format(name=self.get_filepath())

    def get_filepath(self):
        return self.filepath

    def get_filename(self):
        return self.get_filepath().split('/')[-1]

    def get_extension(self):
        return path.get_extension(self.get_filepath())

    def get_fileroot(self):
        return path.fix_path('/'.join(self.get_filepath().split('/')[:-1]))

    def get_project(self):
        from core import db
        p = self.get_filepath()
        if 'projects' in p:
            p = path.fix_path(p)
            elems = p.split('/')
            index = elems.index('projects')
            p_name = elems[index + 2]
            return db.Db().get_project(p_name)
        else:
            return None

    def get_shot(self):
        logger.debug(self.get_fileroot())
        if 'shots' in self.get_fileroot():
            elems = self.get_filepath().split('/')
            index = elems.index('shots')
            s_name = elems[index+1]
            return self.get_project().get_shot(s_name)
        else:
            return False


class NukeProjectFile(projectFile.ProjectFile):
    '''
    Subclass of ProjectFile for houdini project files
    '''

    def get_nuke_info(self):
        '''
        returns a dictionary of information about the filename
        :return:
        '''
        regex = r'(?P<root>.+)/(?P<compname>\w+)_(?P<version>\w+)(\.(?P<ext>\w+))'

        logger.debug(self.get_filename())

        info = {}
        match = re.match(regex, self.get_filepath())
        info['ver'] = match.group('version')
        info['task'] = 'comp'
        info['scene'] = match.group('compname')
        return info

    def get_version(self):
        return self.get_nuke_info()['ver']


class HoudiniProjectFile(projectFile.ProjectFile):
    '''
    Subclass of ProjectFile for houdini project files
    '''


    def get_hip_info(self):
        '''
        returns a dictionary of information about the filename
        :return:
        '''
        regex = r'^(?P<scene>\w+)-(?P<task>\w+)-(?P<full_ver>v(?P<ver>\d{3,}))(-(?P<desc>\w+))?-(?P<user>\w+)' \
                r'(\.(?P<ext>\w+))$'

        info = {}
        match = re.match(regex, self.get_filename(), flags=re.IGNORECASE)
        info['ver'] = match.group('ver')
        info['task'] = match.group('task')
        info['scene'] = match.group('scene')
        info['user'] = match.group('user')
        return info

    def get_latest_hip_version(self):
        regex = '(?P<scene>{scene})-(?P<task>{task})-v(?P<ver_num>\\d{{3,}})'.format(scene=self.get_hip_info()['scene'],
                                                                                     task=self.get_hip_info()['task'])
        ver_nums = []

        # regex get highest version number from the directory

        for f in self.get_shot().project_files():
            if not os.path.isdir(f.get_path()):

                # logger.debug(f)
                match = re.match(regex, f.name(), flags=re.IGNORECASE)
                if match:

                    # logger.error(f)
                    ver_nums.append(int(match.group('ver_num')))

        return ver_nums
