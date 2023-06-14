import PySimpleGUI as sg
from utility import logger
from utility import config
from core import db
from utility import osutil
from ui import projManager
from ui import add_shot


def shot_manager(project_name):
    # get information
    vals = []
    d = db.Db()
    project = d.get_project(project_name)
    shots = project.get_shots(database=d)

    # sort by date
    shots.sort(key=lambda Shot: Shot.name, reverse=True)

    for s in shots:
        vals.append([s.name, s.frame_start, s.frame_end,
                     0])

    headings = ['Name', 'Start Frame', 'End Frame', 'Size(MB)']

    title = '{0} Database'.format(project.name)

    sg.theme(config.THEME)
    contact_information_array = vals
    logger.debug(vals)
    layout = [
        [sg.Text(title, justification='center', font='Arial 30 bold', size=(30,1))],
        [sg.Table(values=contact_information_array,
                  headings=headings,
                  max_col_width=35,
                  auto_size_columns=True,
                  display_row_numbers=False,
                  justification='c',
                  bind_return_key=True,
                  num_rows=10,
                  key='-TABLE-',
                  row_height=35,
                  enable_click_events=True,
                  font='Helvetica 15')],
        [
            sg.Button('Back', size=(10, 1), font='Helvitica 20', key='-BACK-'),
            sg.Button('Add Shot', size=(10, 1), font='Helvitica 20', key='-ADDSHOT-')
        ]
    ]

    window = sg.Window(title, layout)

    while True:
        event, values = window.read()

        # Get selection
        selection = []
        for sel in values['-TABLE-']:
            selection.append(vals[sel])
            logger.debug(selection)

        if event == "Exit" or event == sg.WIN_CLOSED or event == '-BACK-':
            break

        if event == '-TABLE-':
            for s in selection:
                s = project.get_shot(s[0])
                osutil.open_dir('{0}/'.format(s.get_project_path()))

        if event == '-ADDSHOT-':
            break

        logger.debug(event)

    window.close()

    if event == '-BACK-':
        logger.warning(event)
        return projManager.db_manager()

    if event == '-ADDSHOT-':
        logger.warning(event)
        return add_shot.add_shot(project)

    if event == 'Exit' or event == sg.WIN_CLOSED:
        logger.debug('Exit button pressed')
        return None

    if not values['-TABLE-']:
        logger.debug('Nothing selected.')
        return None

    selection = []
    for sel in values['-TABLE-']:
        selection.append(vals[sel])
        logger.debug(selection)

    return selection
