# smatterscripts

Scripts that cover a smattering of functionality I need to use from time to time.

## Installation

Clone the repository and execute `ant install` from the project root. This 
generates executable scripts in `bin/` and links to them in `$HOME/.local/bin`.

To add that directory to your `PATH` environment variable, edit `$HOME/.bashrc`
and add these lines:

    if [ -d "$HOME/.local/bin" ] ; then
        PATH="$HOME/.local/bin:$PATH"
    fi

To overwrite existing links in `.local/bin`, execute:

    $ ant -Dinstall.overwrite=true install

## Adding a program to the set of installed files

Add a macro to generate the script in the `compile` target:

    <generate-script relpath="path/to/foo.py">foo</generate-script>

Add a macro to create the symbolic link:

    <install-script>histo</install-script>
