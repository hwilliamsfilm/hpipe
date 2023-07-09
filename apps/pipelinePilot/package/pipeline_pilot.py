from PySide2 import QtWidgets


class ProjectTreeView(QtWidgets.QWidget):
    """
    Tree view of the project database.
    """
    def __init__(self):
        super(ProjectTreeView, self).__init__()
        self.layout = QtWidgets.QVBoxLayout()
        # add some buttons
        self.layout.addWidget(QtWidgets.QPushButton('Project'))
        self.layout.addWidget(QtWidgets.QPushButton('Shot'))
        self.layout.addWidget(QtWidgets.QPushButton('Asset'))
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


class ProjectSidebar(QtWidgets.QWidget):
    """
    Sidebar of the project database.
    """
    def __init__(self):
        super(ProjectSidebar, self).__init__()
        self.layout = QtWidgets.QVBoxLayout()
        # add some buttons
        self.layout.addWidget(QtWidgets.QPushButton('Create Project'))
        self.layout.addWidget(QtWidgets.QPushButton('Create Shot'))
        self.layout.addWidget(QtWidgets.QPushButton('Create Asset'))
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


class TopBar(QtWidgets.QWidget):
    """
    Top bar of the project database.
    """
    def __init__(self):
        super(TopBar, self).__init__()
        self.layout = QtWidgets.QHBoxLayout()
        # add some dropdowns
        self.layout.addWidget(QtWidgets.QPushButton('File'))
        self.layout.addWidget(QtWidgets.QPushButton('Edit'))
        self.layout.addWidget(QtWidgets.QPushButton('View'))
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)


class BottomBar(QtWidgets.QWidget):
    """
    Bottom bar of the project database.
    """
    pass


class MainView(QtWidgets.QWidget):
    """
    Global view of the project database.
    """
    def __init__(self):
        super(MainView, self).__init__()
        self.setWindowTitle('Pipeline Pilot')
        self.resize(1920, 1080)
        self.setWindowOpacity(0.99)

        self.contents_layout = QtWidgets.QHBoxLayout()
        self.contents_layout.addLayout(ProjectTreeView())
        self.contents_layout.addLayout(ProjectSidebar())

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addLayout(TopBar())
        self.main_layout.addLayout(self.contents_layout)
        self.main_layout.addLayout(BottomBar())

