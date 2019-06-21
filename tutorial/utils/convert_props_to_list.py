# -*- coding: utf-8 -*-
import dash_html_components as html
import dash_core_components as dcc
import re
from textwrap import dedent


def generate_prop_info(component_name, lib=dcc):
    component = getattr(lib, component_name)
    component_doc = component.__doc__

    regex = r'''^(.*?)\s*\((.*?);*\s*([\w\s'"().]*)\):\s*(.*?)\s*$'''

    return_div = [
        dcc.Markdown(dedent(
            '''
            > Access this documentation in your Python terminal with:
            > ```
            > >>> help({}.{})
            > ```
            '''.format(lib.__name__, component_name)
        ))
    ]

    props = component_doc.split('\n-')[1:]

    # sort alphabetically, but keep id at the top
    id_prop = props.pop(0)
    props.sort(key=lambda x: x.strip()[0])
    props = [id_prop] + props

    for prop in props:

        r = re.match(
            re.compile(regex),
            prop.replace('\n', ' ')
        )

        if r is not None:
            (prop_name, prop_type, prop_optional_default, prop_desc) = r.groups()
            prop_desc = prop_desc.replace('[', '\[').replace(']', '\]')

            if 'dict containing keys' in prop_desc:
                regex_dict = r'''.*\. [\w]* has the following type: (?:[\w\s|]*)dict containing keys ([\w\s',]*). Those keys have the following types: ([\w\s|();:',.-]*)'''
                try:
                    top_level_keys = re.match(
                        re.compile(regex_dict),
                        prop_desc
                    ).groups(1)[0]
                    key_defs = re.match(re.compile(regex_dict), prop_desc).groups(1)[1]
                    top_level_keys = [key.strip().strip('\'')
                                      for key in top_level_keys.split(',')]
                    for key in top_level_keys:
                        key_defs = key_defs.replace(f'- {key}', f'\n- {key}', 1)
                        prop_desc_list = ''.join(key_defs)
                    prop_desc = prop_desc_list
                except AttributeError:
                    pass

            defined_default_val = re.search(
                r'''default ([\w\s'.()"]*)''',
                prop_optional_default
            )

            prop_optional = prop_optional_default
            if defined_default_val is not None:
                default_val = defined_default_val.groups(1)[0]
                prop_optional = f'default `{default_val}`'

            return_div.append(dcc.Markdown(dedent(
                f'''**`{prop_name}`** (*{prop_type};* {prop_optional}): {prop_desc}'''
            )))

    return html.Div(return_div)
