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

Add a macro to generate the executable script in the `compile` target:

    <generate-executable module="mod.foo">foo</generate-script>

This creates a launcher program in the `launchers` module and an executable
script in `/bin`.

Then add a macro to create the symbolic link on your local filesystem:

    <install-script>foo</install-script>

This creates a symbolic link in `$HOME/.local/bin`. To create the link 
elsewhere, specify the destination as the `install_dir` property:

    $ ant -Dinstall_dir=/path/somewhere/else install

