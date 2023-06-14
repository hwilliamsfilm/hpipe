import PySimpleGUI as sg
from utility import logger
from utility import config


def simple_text(text):
    sg.theme(config.THEME)
    layout = [[sg.Text(text)],
              [sg.InputText(key='-IN-')],
              [sg.Submit(), sg.Cancel()]]

    window = sg.Window('Window Title', layout)

    event, values = window.read()
    logger.info('Closed window')
    window.close()
    return values['-IN-']


def simple_list(title, message, list_items):
    sg.theme(config.THEME)
    layout = [[sg.Text(title, size=(10,1), font='Helvitica 50', justification='l')],
              [sg.Text(message)],
              [sg.Listbox(values=list_items, size=(40, 10), key='-LIST-', font='Helvitica 20', enable_events=True)],
              [sg.Button('Enter', size=(10,1), font='Helvitica 30'), sg.Button('Exit', size=(10,1), font='Helvitica 30')]]

    window = sg.Window('Project Manager', layout)

    while True:  # Event Loop
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        elif event in (sg.WIN_CLOSED, 'Enter'):
            break
    window.close()

    try:
        selection = values['-LIST-'][0]
        return selection
    except IndexError:
        return None


def simple_table(title, headings, vals):
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
        [sg.Button('Enter', size=(10,1), font='Helvitica 20'), sg.Button('Exit', size=(10,1), font='Helvitica 20')]
    ]

    window = sg.Window(title, layout)

    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        elif event in (sg.WIN_CLOSED, 'Enter'):
            break
        if event == '-TABLE-':
            break

        logger.debug(event)

    window.close()

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

