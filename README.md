# smatterscripts

Scripts that cover a smattering of functionality I need to use from time to time.

## Installation

### Steps

    $ git clone https://github.com/mike10004/smatterscripts.git
    $ cd smatterscripts
    $ ant install

### Explanation

Clone the repository and execute `ant install` from the project root. This 
generates executable scripts in `bin/` and links to them in `$HOME/.local/bin`.

To add that directory to your `PATH` environment variable, edit `$HOME/.bashrc`
and add these lines:

    if [ -d "$HOME/.local/bin" ] ; then
        PATH="$HOME/.local/bin:$PATH"
    fi

To overwrite existing links in `.local/bin`, execute:

    $ ant -Dinstall.overwrite=true install

## Uninstallation

    $ cd <smatterscripts_repo_dir>
    $ ant uninstall

## Programs

* **smhisto** print histogram from CSV input data
* **smhtmljux** generate HTML page from CSV file to compare images side-by-side
* **smclusters** find clusters of graph input data in CSV 
* **smcsv2sortable** format data for GNU **sort**
* **smressample** randomly sample lines from an input stream
* **smstreamproduct** concatenate lines from multiple input files

## For Developers

### Adding a program to the set of installed files

Add a macro to generate the executable script in the `compile` target:

    <generate-executable module="mod.foo">foo</generate-script>

This creates a launcher program in the `launchers` module and an executable
script in `/bin`.

Then add a macro to create the symbolic link on your local filesystem:

    <install-script>foo</install-script>

This creates a symbolic link in `$HOME/.local/bin`. To create the link 
elsewhere, specify the destination as the `install_dir` property:

    $ ant -Dinstall_dir=/path/somewhere/else install

