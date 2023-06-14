import PySimpleGUI as sg
from utility import logger
from utility import config
from core import db, shot
from utility import size
from utility import osutil
from utility import path
from ui import projManager
from ui import popup
from asset import sequence


def sequence_manager(sequences):

    # get information

    headings = ['Name', 'Type', 'Frame Count']

    title = 'sequences'

    sg.theme(config.THEME)
    vals = [['/'.join(s.get_filepaths()[0].split(r'/')[-2:]), s.get_extension(), s.get_total()] for s in sequences]
    logger.debug(vals)
    column = [
        [sg.Text(title, justification='center', font='Arial 30 bold', size=(30,1))],
        [sg.Table(values=vals,
                  headings=headings,
                  max_col_width=35,
                  auto_size_columns=True,
                  display_row_numbers=False,
                  justification='l',
                  bind_return_key=True,
                  num_rows=10,
                  key='-TABLE-',
                  row_height=35,
                  enable_events=True,
                  font='Helvetica 15',
                  expand_x=True,
                  expand_y=True)],
        [
            sg.Button('Back', size=(10, 1), font='Helvitica 20', key='-BACK-'),
            sg.Button('Convert to QT', size=(10, 1), font='Helvitica 20', key='-Convert-'),
            sg.Button('Contact Sheet', size=(10, 1), font='Helvitica 20', key='-Contact-'),
            sg.Button('INFO', size=(10, 1), font='Helvitica 20', key='-GETINFO-')
        ]
    ]
    info = ['Frames:', 'Type:', 'Channels:']
    column2 = [
        [sg.Table(values=vals,
                  headings=headings,
                  max_col_width=35,
                  auto_size_columns=True,
                  display_row_numbers=False,
                  justification='l',
                  bind_return_key=True,
                  num_rows=10,
                  key='-TABLE-',
                  row_height=35,
                  enable_events=True,
                  font='Helvetica 15',
                  expand_x=True,
                  expand_y=True)]
        ]

    col1 = sg.Column(column)
    layout = [[col1]]

    window = sg.Window(title, layout,  resizable=True, finalize=True, icon=r'Y:\_houdini_\icons\main.png',
                       alpha_channel=.95)
    locked = True

    col1.expand(True, True)

    while True:
        event, values = window.read()

        # Get selection
        selection = []
        for sel in values['-TABLE-']:
            for s in sequences:
                s_name = '/'.join(s.get_filepaths()[0].split(r'/')[-2:])
                if vals[sel][0] == s_name:
                    logger.warning(s)
                    logger.warning(s.get_filename())
                    selection.append(s)
            logger.debug(selection)

        if event == "Exit" or event == sg.WIN_CLOSED or event == '-BACK-':
            break

        if event == '-Convert-':
            logger.info(selection)
            for s in selection:
                if s.get_extension() == 'exr':
                    chan = popup.simple_text('Channel:')
                    s.to_jpg(chan).to_qt()
                if s.get_extension() == 'png':
                    s.to_qt()
                if s.get_extension() == 'jpg':
                    s.to_qt()

        if event == '-Contact-':
            logger.info(selection)
            if len(selection) == 4:
                logger.warning('contactSheet command')
                logger.info(selection)
                sequence.GeneralImageSequence.create_contact_sheet(selection)

        if event == '-GETINFO-':
            for s in selection:
                #logger.info(s)
                info = s.get_info(s.get_filepaths()[0])
                logger.info(info)

    window.close()

    if event == '-BACK-':
        return projManager.db_manager()