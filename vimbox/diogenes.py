# FONT_COLORORS
FONT_COLOR = {
    'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34,
    'magenta': 35, 'cyan': 36, 'light gray': 37, 'dark gray': 90,
    'light red': 91, 'light green': 92, 'light yellow': 93,
    'light blue': 94, 'light magenta': 95, 'light cyan': 96, 'white': 97
}

# BG FONT_COLORORS
BACKGROUND_COLOR = {
    'black': 40,  'red': 41, 'green': 42, 'yellow': 43, 'blue': 44,
     'magenta': 45, 'cyan': 46, 'light gray': 47, 'dark gray': 100,
     'light red': 101, 'light green': 102, 'light yellow': 103,
     'light blue': 104, 'light magenta': 105, 'light cyan': 106,
     'white': 107
}

# TODO: Recover this
STYLE = {}


def color(text, font_color=None, background_color=None, style=None):
    '''
    Wraps string in ANSI scape sequs to display color in command line
    '''

    if style:
        if style not in STYLE:
            raise ValueError("Unknown ANSI style %s" % style)
        text = "\033[%dm%s\033[0m" % (STYLE[style], text)
    if font_color:
        if font_color not in FONT_COLOR:
            raise ValueError("Unknown ANSI color %s" % font_color)
        text = "\033[%dm%s\033[0m" % (FONT_COLOR[font_color], text)
    if background_color:
        if background_color not in BACKGROUND_COLOR:
            raise ValueError(
                "Unknown ANSI background color %s" % background_color
            )
        text = "\033[%dm%s\033[0m" % (BACKGROUND_COLOR[background_color], text)

    return text


def style(font_color=None, background_color=None):
    def apply_style(text):
        return color(
            text,
            font_color=font_color,
            background_color=background_color
        )
    return apply_style
