import argparse
import os
import re
from pathlib import Path

# from GCC documentation
CPP_HEADER_EXTENSIONS = {'.hh', '.H', '.hp', '.hxx', '.hpp', '.HPP', '.h++', '.tcc', ''}
C_HEADER_EXTENSIONS = {'.h'}

def guard_name_parent_plus_name(filename: str):
    """
    Create a header guard name composed of the parent folder names (below src)
    and the filename.

    Parameters
    ----------
    filename : str
        The name of the file containing the header guard

    Returns
    -------
    str
        The header guard
    """
    name = filename
    # Remove 'src' folder as well as relative parent folders
    name = re.sub(r'^src/', '', name)
    name = re.sub(r'^\\.\\./', '', name)
    name = re.sub(r'^\\./', '', name)

    name = re.sub(r'[^0-9a-zA-Z_]', '_', name)
    return name.upper()


def guard_name_project_plus_name(filename: str, project_name: str):
    """
    Create a header guard name composed of a project name the filename.

    Parameters
    ----------
    filename : str
        The name of the file containing the header guard
    project_name : str
        The name of the C++ project to add to the header guard

    Returns
    -------
    str
        The header guard
    """
    path = Path(filename)
    if project_name:
        return f"{project_name}_{path.stem}_H".upper()
    return f"{path.stem}_H".upper()


def vim_file_type(filename):
    _, extension = os.path.splitext(filename)
    if extension in CPP_HEADER_EXTENSIONS: return 'cpp'
    if extension in C_HEADER_EXTENSIONS: return 'c'
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description='Check and add C/C++ header guard')
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    parser.add_argument('--project_name', nargs=1, help="")
    args = parser.parse_args(argv)
    guard = re.compile(r'#ifndef\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\n\s*#define\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\n')
    ret = 0

    for filename in args.filenames:
        contents = None
        with open(filename) as f:
            contents = f.read();

        if args.project_name:
            name = guard_name_project_plus_name(filename, args.project_name[0])
        else:
            name = guard_name_parent_plus_name(filename)

        m = guard.match(contents)
        if m:
            name1 = m.group(1)
            name2 = m.group(2)
            if name1 == name2 and name1 != name:
                # update header guard
                with open(filename, 'w') as f:
                    f.write(contents[:m.start(1)])
                    f.write(name)
                    f.write(contents[m.end(1):m.start(2)])
                    f.write(name)
                    f.write(contents[m.end(2):])
                print('{}: rename header guard'.format(filename))
                ret = 1
        else:
            # add header guard
            with open(filename, 'w') as f:
                f.write(f'#ifndef {name}\n#define {name}\n\n')
                f.write(contents)
                f.write(f'\n#endif  // {name}')
                filetype = vim_file_type(filename)
                if filename is not None:
                    f.write(' // vim' + ':filetype=')
                    f.write(filetype)
                f.write('\n')
            print('{}: add header guard'.format(filename))
            ret = 1
    return ret

if __name__ == '__main__':
    exit(main())
