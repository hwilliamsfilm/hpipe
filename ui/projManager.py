import PySimpleGUI as sg

import ui.sequenceManager
from utility import logger
from utility import config
from core import db
from utility import size
from utility import osutil
from ui import shotManager
import pprint
import re
import json


def db_manager():

    # get information
    vals = []
    d = db.Db()
    d.backup_db()
    projects = d.get_projects()

    # sort by date
    projects.sort(key=lambda project: project.date, reverse=True)

    for p in projects:
        vals.append([p.name, ', '.join([s.name for s in p.get_shots(database=d)]), p.date,
                     round(0)])    # round(size.get_size(p.get_project_path())

    headings = ['Name', 'Shots', 'Date Created', 'Size(MB)']

    title = 'PROJECT DATABASE'
    sg.theme(config.THEME)

    # COLUMN 01
    column_01 = [
        [sg.Text(title, justification='left', font='Arial 30 bold', size=(43,1))],
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
                  font='Helvetica 15', expand_x=True, expand_y=True)],
        [
            sg.Button('Shots', size=(10, 1), font='Helvitica 20', key='-BROWSE-'),
            sg.Button('Create Delivery', size=(10, 1), font='Helvitica 20', key='-PROJ_DIR-'),
            sg.Button('Asset-dir', size=(10, 1), font='Helvitica 20', key='-ASSET_DIR-'),
            sg.Button('Delivery-dir', size=(10, 1), font='Helvitica 20', key='-DELIV_DIR-'),
            sg.Button('New Project', size=(10, 1), font='Helvitica 20', key='-NEWPROJ-'),
        ],
        [
            sg.Button('Backup', size=(10, 1), font='Helvitica 20', key='-BACKUP-'),
            sg.Button('Log Time', size=(10, 1), font='Helvitica 20', key='-LOGTIME-'),
            sg.Button('Archive', size=(10, 1), font='Helvitica 20', key='-ARCHIVE-'),
            sg.Button('Copy', size=(10, 1), font='Helvitica 20', key='-COPY-'),
            sg.Button('Sequences', size=(10, 1), font='Helvitica 20', key='-SEQ-'),
        ]

    ]

    # COLUMN 02
    column_02 = [
        [sg.Multiline(size=(60,25), font='Helvetica 15 bold', key='-OUTPUT-', enable_events=True, disabled=True, background_color='#282829', expand_x=True, expand_y=True)],
        [
            sg.Button('Update', size=(10, 1), font='Helvitica 20', key='-UPDATE-'),
            sg.Button('Refresh', size=(10, 1), font='Helvitica 20', key='-REFRESH-'),
            sg.Button('Locked', size=(10, 1), font='Helvitica 20', key='-LOCK-')
        ]
    ]
    sg.Multiline()
    col1 = sg.Column(column_01)
    col2 = sg.Column(column_02)
    layout = [
        [col1,
         sg.VSeperator(),
         col2, ]
    ]

    window = sg.Window(title, layout,  resizable=True, finalize=True, icon=r'Y:\_houdini_\icons\main.png',
                       alpha_channel=.95)
    locked = True

    col1.expand(True, True)
    col2.expand(True, True)

    # UI LOOP
    while True:
        event, values = window.read()
        # BUTTONS
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        database = d

        selection = []
        # TABLE STUFF
        if values['-TABLE-']:
            # Get selection
            for sel in values['-TABLE-']:
                selection.append(vals[sel])


        if event == '-LOCK-':
            if locked:
                window.Element('-LOCK-').update('Unlocked')
                window['-OUTPUT-'].update(disabled=False)
                window['-OUTPUT-'].update(background_color=sg.theme_button_color()[1])
                locked = False
            else:
                window.Element('-LOCK-').update('Locked')
                window['-OUTPUT-'].update(disabled=True, background_color='#282829')
                locked = True

        if event == '-TABLE-':
            p = database.get_project(selection[0][0]).export_project(database)
            window['-OUTPUT-'].update(json.dumps(p, sort_keys=True, indent=8))

        if event == '-UPDATE-':
            if values['-TABLE-']:
                s_info = vals[values['-TABLE-'][0]]

            database = db.Db()
            project = db.Db().get_project(s_info[0])

            if project:
                dict1 = json.loads(values['-OUTPUT-'])
                dict2 = database.get_project_as_dict(s_info[0])

                def findDiff(d1, d2, path=""):
                    for k in d1:
                        if k in d2:
                            if type(d1[k]) is dict:
                                findDiff(d1[k], d2[k], "[%s/%s]" % (path, k) if path else k)
                                continue
                            if d1[k] != d2[k]:
                                result = ["%s: " % path, " DB %s : %s -->" % (k, d2[k]), " TXT %s : %s" % (k, d1[k])]
                                logger.info(" ".join(result))
                        else:
                            logger.info("%s%s as key not in DB\n" % ("%s: " % path if path else "", k))

                findDiff(dict1, dict2)

                database.update_project(s_info[0], dict1)
                database = db.Db()
                p = database.get_project(selection[0][0]).export_project(database)
                window['-OUTPUT-'].update(json.dumps(p, sort_keys=True, indent=8))

        if event == '-BROWSE-' and len(selection) > 0:
            break

        # DIRECTORIES
        if event == '-ASSET_DIR-':
            for p in selection:
                p = database.get_project(p[0])
                osutil.open_dir('{0}/'.format(p.get_assets_path()))

        if event == '-PROJ_DIR-':
            for p in selection:
                p = database.get_project(p[0])
                osutil.open_dir('{0}/'.format(p.get_project_path()))

        if event == '-DELIV_DIR-':
            for p in selection:
                p = database.get_project(p[0])
                osutil.open_dir('{0}/'.format(p.get_delivery_path()))

        if event == '-NEWPROJ-':
            break

        if event == '-REFRESH-':
            database = db.Db()
            p = database.get_project(selection[0][0]).export_project(database)
            window['-OUTPUT-'].update(json.dumps(p, sort_keys=True, indent=8))

        if event == '-SEQ-':
            break

        logger.debug(event)

    window.close()

    selection = []
    if values:
        if values['-TABLE-']:
            for sel in values['-TABLE-']:
                selection.append(vals[sel])
                logger.debug(selection)

    if len(selection) > 0 and event == '-BROWSE-':
        from ui import shotManager
        logger.info(selection)
        shotManager.shot_manager(selection[0][0])

    if event == '-NEWPROJ-':
        from ui import add_project
        add_project.add_project()

    if event == '-SEQ-':
        from ui import sequenceManager
        from utility import path
        p = database.get_project(selection[0][0])
        sequences = []
        for s in p.get_shots(database):
            spath = s.get_render_path(database)
            logger.info(spath)
            sequences += path.get_image_dirs(spath)
        logger.info(sequences)
        sequenceManager.sequence_manager(sequences)