class ProjectNotFound(Exception):
    """Exception raised for errors in the input salary.

    Attributes:
        salary -- input salary which caused the error
        message -- explanation of the error
    """

    def __init__(self, project_name, message="Project not found!"):
        self.project_name = project_name
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.project_name} -> {self.message}'


class ShotNotFound(Exception):
    """Exception raised for errors in the input salary.

    Attributes:
        salary -- input salary which caused the error
        message -- explanation of the error
    """

    def __init__(self, shot_name, message="Shot not found!"):
        self.shot_name = shot_name
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.shot_name} -> {self.message}'

class ProjectFileType(Exception):
    """Exception raised for errors in the input salary.

    Attributes:
        salary -- input salary which caused the error
        message -- explanation of the error
    """

    def __init__(self, path, message="Project file not correct type!"):
        self.path = path
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.path} -> {self.message}'
