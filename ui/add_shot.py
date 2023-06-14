from core import db
import PySimpleGUI as sg
from utility import logger
from utility import config
from ui import shotManager


def add_shot(project=None):
    sg.theme(config.THEME)
    layout = [[sg.Text('Project Name:', font='Helvetica 20'),
               sg.InputText(size=(50, 30), font='Helvetica 20', key='-PNAME-')],
              [sg.Text('Shot Name:             ', font='Helvetica 20'),
               sg.InputText(size=(50, 30), font='Helvetica 20', key='-SNAME-')],
              [sg.Text('FSTART:    ', font='Helvetica 20'),
               sg.InputText(size=(50, 30), font='Helvetica 20', key='-FSTART-')],
              [sg.Text('FEND:    ', font='Helvetica 20'),
               sg.InputText(size=(50, 30), font='Helvetica 20', key='-FEND-')],
              [sg.Button('Submit', enable_events=True, font='Helvetica 20', key='-SUBMIT-'), sg.Cancel(font='Helvetica 20')]]

    if project:
        layout = [[sg.Text('Shot Name:             ', font='Helvetica 20'),
                   sg.InputText(size=(50, 30), font='Helvetica 20', key='-SNAME-')],
                  [sg.Text('FSTART:    ', font='Helvetica 20'),
                   sg.InputText(size=(50, 30), font='Helvetica 20', key='-FSTART-')],
                  [sg.Text('FEND:    ', font='Helvetica 20'),
                   sg.InputText(size=(50, 30), font='Helvetica 20', key='-FEND-')],
                  [sg.Button('Submit', enable_events=True, font='Helvetica 20', key='-SUBMIT-'), sg.Cancel(font='Helvetica 20')]]

    window = sg.Window('Create Project', layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == '-SUBMIT-':
            if values['-SNAME-']:
                break
        if event == 'Cancel':
            break

    window.close()

    logger.info(event)
    logger.info(values)

    if event == '-SUBMIT-':
        if values['-SNAME-']:
            d = db.Db()
            if not project:
                project = d.get_project(values['-PNAME-'])
            logger.info(project)
            project.create_shot(values['-SNAME-'], frame_start=int(values['-FSTART-']), frame_end=int(values['-FEND-']))
            return shotManager.shot_manager(project.name)
    else:
        return shotManager.shot_manager(project.name)
