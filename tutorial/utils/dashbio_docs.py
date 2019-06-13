import re
import os
import sys

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bio

if __name__ != '__main__':
    from tutorial import styles
    from tutorial.utils.component_block import ComponentBlock
    from tutorial.utils.convert_props_to_table import generate_prop_info
else:
    from convert_props_to_table import js_to_py_type

from textwrap import dedent as s

import json



# all component names

def get_component_names(library_name):
    '''Gets the names of all components, Python and React, in a library.

    :param (str) library_name: The name of the library for which to
    obtain component names.

    '''

    exec("import {}".format(library_name))

    library = eval(library_name)
    members = dir(library)

    all_components = [member for member in members if re.search(
        r'^[A-Z][a-zA-Z]+$', member
    ) is not None]

    react = [c.__name__ for c in library._components]
    python = [c for c in all_components if c not in react]

    return {'react': react,
            'python': python}


# code containers

def IframeComponentBlock(
        example_string,
        location,
        height=600,
        width=600
):
    '''Generate a container that is visually similar to the
    ComponentBlock for components that require an externally hosted app.

    :param (str) example_string: String containing the code that is
    used in the application from the iframe.
    :param (str) location: The URL of the app.
    :param (int) height: The height of the iframe.
    :param (int) width: The width of the iframe.

    :rtype (dict): A dash_html_components div containing the code
    container and the iframe.

    '''

    return html.Div([
        dcc.SyntaxHighlighter(
            example_string,
            language='python',
            customStyle=styles.code_container
        ),
        html.Div(
            className='example-container',
            children=html.Iframe(
                width='{}px'.format(width),
                height='{}px'.format(height),
                style={'border': 'none'},
                src=location
            )
        )
    ])


def generate_component_example(
        component_name,
        library_name, library_short,
        description='',
        params=None,
        style=None,
        default_id=True,
        datafile=None,
        library_imports=None,
        setup_code='',
        component_wrap=None,
        iframe_info=None
):
    '''Generate an example for a component, with hyperlinks to the
    appropriate component-specific pages.

    :param (str) component_name: The name of the component as it is
    defined within the package.
    :param (str) library_name: The full name of the library (e.g.,
    dash_bio).
    :param (str) library_short: The short name of the library, used in an
    import statement (i.e., import library_name as library_short).
    :param (str) description: A short string describing the component.
    :param (dict) params: A dictionary that contains the parameters
    assigned to the component that is to be displayed as a live
    example; the keys correspond to the parameter names.
    :param (dict) style: A dictionary that contains any style
    options. The keys correspond to the style parameter names.
    :param (bool) default_id: Whether or not to assign a default ID to
    the component in the example code.
    :param (string) datafile: The name of the data file, if any, used
    for the component. This file should be present in the folder
    specified by the variable DATA_LOCATION_PREFIX.
    :param (list[list]) library_imports: A list for which each element
    is a list with two elements: the first element should be the full
    name of the library, and the second element should be the short
    name of the library. Contains all of the libraries necessary for
    running the example code (e.g., pandas).
    :param (str) setup_code: Any additional code required before
    rendering the component (e.g., parsing a data file).
    :param (str) component_wrap: A string that will wrap the component
    (e.g., if the component needs to be an argument for a dcc.Graph).
    The location of the component code is represented by an
    underscore (_).
    :param (dict) iframe_info: The URL and, if applicable, the height
    and width of the iframe containing the example.
    :rtype (list[obj]): A list containing the entire section for the
    component in question, including the code block, component demo,
    description, and hyperlinks to the component-specific page.
    '''

    # location of all sample data
    DATA_LOCATION_PREFIX = '''https://raw.githubusercontent.com/plotly/\
dash-bio/master/tests/dashbio_demos/sample_data/'''

    if library_imports is None:
        library_imports = []

    # parameters for initial declaration of component
    paramstring = '\n  '

    if default_id is True:
        paramstring += 'id=\'my-{}-{}\', '.format(
            library_short,
            component_name.lower())

    if params is not None:
        for key in params.keys():
            paramstring += '{}={}, '.format(key, params[key])

    # style options
    if style is not None:
        styleString = 'style={\n  '
        for key in style.keys():
            styleString += '  \'{}\': \'{}\', '.format(
                key,
                str(style[key])
            )

        # remove comma and space following the last style option
        styleString = styleString[:-2]

        styleString += '\n  }, '
        paramstring += styleString

    # loading data if necessary
    if datafile is not None:
        library_imports.append(
            ['urllib.request', 'urlreq']
        )

        # only decode for python 3
        decode_string = ''
        if sys.version_info >= (3, 0):
            decode_string = '.decode(\"utf-8\")'

        # add data location
        setup_code = '''\ndata = urlreq.urlopen(\"{}{}\").read(){}
'''.format(
            DATA_LOCATION_PREFIX,
            datafile['name'],
            decode_string
        ) + setup_code

        # declare data in component initialization if necessary
        if 'parameter' in datafile.keys():
            paramstring += '{}=data, '.format(
                datafile['parameter']
            )

    # pretty-print param string (spaces for indentation)
    paramstring = paramstring.replace(', ', ',\n  ')

    # remove the characters following the final parameter
    # (',\n  '), and add unindented newline at end
    if(len(paramstring) > 4):
        paramstring = paramstring[:-4] + '\n'
    # if no params were supplied, remove all newlines
    else:
        paramstring = ''

    # format component string
    component_string = '{}.{}({})'.format(
        library_short,
        component_name,
        paramstring
    )
    # wrap component if necessary
    if component_wrap is not None:
        component_string = component_wrap.replace(
            '_', component_string)

    # add imports
    imports_string = ''
    for library in library_imports:
        if library[0] != library[1]:
            imports_string += 'import {} as {}\n'.format(
                library[0],
                library[1]
            )
        else:
            imports_string += 'import {}\n'.format(
                library[0]
            )

    # change urllib package if necessary (due to Python version)
    if sys.version_info < (3, 0):
        imports_string = imports_string.replace('urllib.request', 'urllib2')

    # full code
    example_string = '''import {} as {}
{}
{}
component = {}
'''.format(library_name,
           library_short,
           imports_string,
           setup_code,
           component_string)


    # load the iframe if that is where the app is
    if iframe_info is not None:
        component_demo = IframeComponentBlock(
            example_string,
            **iframe_info
        )
    else:
        component_demo = ComponentBlock(
            example_string
        )

    # full component section
    return [

        html.Hr(),

        html.H3(dcc.Link(component_name,
                         href='/{}/{}'.format(
                             library_name.replace('_', '-'),
                             component_name.lower())),
                id=component_name.replace(' ', '-').lower()),

        dcc.Markdown(s(description)),

        component_demo,

        html.Br(),

        dcc.Link('More {} Examples and Reference'.format(component_name),
                 href='/{}/{}'.format(
                     library_name.replace('_', '-'),
                     component_name.lower()))
    ]


# full documentation page for library

def generate_docs(
        library_name,
        library_short,
        library_heading,
        library_install_instructions,
        library_components
):
    '''Generate full documentation for a library.

    :param (str) library_name: The full name of the library (e.g.,
    dash_bio).
    :param (str) library_short: The short name of the library, used in an
    import statement (i.e., import library_name as library_short).
    :param (obj) library_heading: A dcc.Markdown object that will be
    at the top of the documentation page; it should provide a brief
    description of the library.
    :param (obj) library_install_instructions: A dcc.SyntaxHighligher
    object that contains the code needed to install the library.
    :param (dict[dict]) library_components: A dictionary for which the
    keys are the names of the components that are to be displayed, and
    the values are dictionaries that can be used by the function
    generate_component_example.

    :rtype (list[object]): The children of the layout for the
    documentation page.

    '''

    layout_children = library_heading

    layout_children.append(library_install_instructions)

    sorted_keys = list(library_components.keys())
    sorted_keys.sort()

    for component in sorted_keys:
        layout_children += generate_component_example(
            component,
            library_name,
            library_short,
            **library_components[component]
        )

    return layout_children


# individual componaent pages

def create_default_example(
        component_name,
        example_code,
        styles
):
    '''Generate a default example for the component-specific page.

    :param (str) component_name: The name of the component as it is
    defined within the package.
    :param (str) example_code: The code for the default example.
    :param (dict) styles: The styles to be applied to the code
    container.

    :rtype (list[object]): The children of the layout for the default
    example.
    '''

    return [
        dcc.Markdown('See {} in action [here](http://dash-bio.plotly.host/dash-{}).'.format(
            component_name.replace('-', ' ').title(),
            component_name
        )),

        html.Hr(),

        html.H3("Default {}".format(
            component_name.replace('-', ' ').title()
        )),
        html.P("An example of a default {} component without \
        any extra properties.".format(
            component_name.replace('-', ' ')
        )),
        dcc.SyntaxHighlighter(
            example_code[0],
        ),
        html.Div(
            example_code[1],
            className='example-container'
        ),
        html.Hr()
    ]


def create_examples(
        examples_data
):
    examples = []
    for example in examples_data:
        examples += [
            html.H3(example['param_name'].title()),
            dcc.Markdown(example['description']),
            ComponentBlock(example['code']),
            html.Hr()
        ]
    return examples


def create_doc_page(examples, component_names, component_name, component_examples=None):
    '''Generates a documentation page for a component.

    :param (dict[object]) examples: A dictionary that contains the
    loaded examples for all components.
    :param (dict[list]) component_names: A dictionary defining which
    components are React components, and which are Python
    components. The keys in the dictionary are 'react' and 'python',
    and the values for each are lists containing the names of the
    components that belong to each category.
    :param (string) component_name: The name of the component in snake
    case, with underscores (_) replaced with dashes (-).

    :rtype (object): A div containing the contents of the component's
    documentation page.
    '''
    c_name = component_name.replace('-', ' ').title().replace(' ', '')

    if component_examples is None:
        component_examples = []
    component_examples = create_examples(component_examples)

    if c_name == 'Molecule3DViewer':
        c_name = 'Molecule3dViewer'

    return html.Div(
        children=[
            html.H1('{} Examples and Reference'.format(
                c_name))] +
        create_default_example(component_name,
                               examples[component_name],
                               styles=styles) +
        component_examples +
        [generate_prop_info(
            c_name,
            lib=dash_bio)]
    )
