import ui.projManager
from core import db, project
from ui import popup
import PySimpleGUI as sg
from utility import logger
from utility import config
from ui import projManager

def add_project():
    sg.theme(config.THEME)
    layout = [[sg.Text('Project Name:', font='Helvetica 20'),
               sg.InputText(size=(50, 30), font='Helvetica 20', key='-NAME-')],
              [sg.Text('Client:             ', font='Helvetica 20'),
               sg.InputText(size=(50, 30), font='Helvetica 20', key='-CLIENT-')],
              [sg.Text('Description:    ', font='Helvetica 20'),
               sg.InputText(size=(50, 30), font='Helvetica 20', key='-DESC-')],
              [sg.Button('Submit', enable_events=True, font='Helvetica 20', key='-SUBMIT-'), sg.Cancel(font='Helvetica 20')]]

    window = sg.Window('Create Project', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == '-SUBMIT-':
            if values['-NAME-']:
                break
        if event == 'Cancel':
            break

    window.close()

    logger.info(event)
    logger.info(values)

    if event == '-SUBMIT-':
        if values['-NAME-']:
            p = project.Project(values['-NAME-'], description=values['-DESC-'])
            db.Db().add_project(p)
            return projManager.db_manager()
    elif event == 'Cancel':
        return projManager.db_manager()
    else:
        return

