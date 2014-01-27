# Pandoc Plugin for Sublime Text 2

A [Sublime Text](http://www.sublimetext.com/) plugin that uses [Pandoc](http://johnmacfarlane.net/pandoc/) to convert text from one markup format into another. Pandoc can convert documents in markdown, reStructuredText, textile, HTML, DocBook, LaTeX, MediaWiki markup, OPML, or Haddock markup to XHTML, HTML5, HTML slide shows using Slidy, reveal.js, Slideous, S5, or DZSlides, Microsoft Word docx, OpenOffice/LibreOffice ODT, OpenDocument XML, EPUB version 2 or 3, FictionBook2, DocBook, GNU TexInfo, Groff man pages, Haddock markup, OPML, LaTeX, ConTeXt, LaTeX Beamer slides, PDF via LaTeX, Markdown, reStructuredText, AsciiDoc, MediaWiki markup, Emacs Org-Mode, Textile, or custom writers can be written in lua.

## Installation

You need to [install Pandoc](http://johnmacfarlane.net/pandoc/installing.html), and this module:

-	[With the Package Control plugin](https://sublime.wbond.net/installation).
-	With Git: Clone the repository in your Sublime Text "Packages" directory:

    	git clone https://github.com/tbfisher/sublimetext-Pandoc.git


	The "Packages" directory is located at:

	* OS X:

	        ~/Library/Application Support/Sublime Text 3/Packages/

	* Linux:

	        ~/.config/sublime-text-3/Packages/

	* Windows:

	        %APPDATA%/Sublime Text 3/Packages/

## Usage

The input format is specified by setting the syntax of the document.

Run Pandoc on the current document via the Command Palette (`Command+Shift+P` on OS X, `Control+Shift+P` on Linux/Windows) by selecting "Pandoc". You will be presented with output formats to choose from.

## Configure

You can fully configure the available formats, and configure the Pandoc options to customize transformation, via the [plugin settings file](http://docs.sublimetext.info/en/latest/customization/settings.html). Via the application menu, go to "Preferences" -> "Package Settings" -> "Pandoc".


