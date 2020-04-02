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
    parser.add_argument('--project-name', nargs=1, help="The project name. When specified the 'project+filename' header guard will be used instead of 'folder+filename' header guard")
    parser.add_argument('--only-missing', action='store_true', help="If provided, header guard is only added if missing")
    parser.add_argument('--add-vim-filetype', action='store_true', help="If provided, add vim filetype when a new header guard is added")
    parser.add_argument('filenames', nargs='*', help='Filenames to check')
    args = parser.parse_args(argv)
    guard = re.compile(r'#ifndef\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\n\s*#define\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\n')
    ret = 0

    for filename in args.filenames:
        contents = None
        with open(filename) as f:
            # We also strip whitespace and newlines in the beginning and in the
            # end
            contents = f.read().strip();
            # but we add a newline at the end
            contents = contents + "\n"

        if args.project_name:
            name = guard_name_project_plus_name(filename, args.project_name[0])
        else:
            name = guard_name_parent_plus_name(filename)
        m = guard.match(contents)
        if m:
            # Add header guard when there is already one, but it is different from what it should be
            name1 = m.group(1)
            name2 = m.group(2)
            # If only_missing argument was provided we do not replace the header guard
            if name1 != name2:
                print(f"Inconsistent header guard in {filename}: '{name1}' and '{name2}'")
                return 1

            if name1 != name and not args.only_missing:
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
            # add header guard when there is None
            with open(filename, 'w') as f:
                f.write(f'#ifndef {name}\n#define {name}\n\n')
                f.write(contents)
                f.write(f'\n#endif  // {name}')
                filetype = vim_file_type(filename)
                if filetype is not None and args.add_vim_filetype:
                    f.write('\n// vim' + ':filetype=')
                    f.write(filetype)
                f.write('\n')
            print('{}: add header guard'.format(filename))
            ret = 1
    return ret

if __name__ == '__main__':
    exit(main())
