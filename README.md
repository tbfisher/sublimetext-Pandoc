# Pandoc

This plugin uses [Pandoc](http://johnmacfarlane.net/pandoc/) to convert text from one markup format into another.

## Installing

You need to [install Pandoc](http://johnmacfarlane.net/pandoc/installing.html), and this module:

**With the Package Control plugin:** The easiest way to install Pandoc is through Package Control, which can be found at this site: http://wbond.net/sublime_packages/package_control

**Without Git:** Download the latest source from [GitHub](https://github.com/tbfisher/Pandoc) and copy the Pandoc folder to your Sublime Text "Packages" directory.

**With Git:** Clone the repository in your Sublime Text "Packages" directory:

    git clone https://github.com/tbfisher/Pandoc.git


The "Packages" directory is located at:

* OS X:

        ~/Library/Application Support/Sublime Text 2/Packages/

* Linux:

        ~/.config/sublime-text-2/Packages/

* Windows:

        %APPDATA%/Sublime Text 2/Packages/

## Usage

The input format is specified by setting the syntax of the document.

Run Pandoc on the current document via the Command Palette (`Command+Shift+P` on OS X, `Control+Shift+P` on Linux/Windows) by selecting "Pandoc". You will be presented with output formats to choose from.

## Configure

In

        Pandoc.sublime-settings

you can fully configure the available formats, and configure the Pandoc options to customize transformation.
