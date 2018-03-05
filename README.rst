==========
phantompy
==========

Headless web-browser with Python API on top of PhantomJS & Selenium (via GhostDriver)

Usage Example
-------------

.. code:: python

    >>> from phantompy import Phantom
    >>> bro = Phantom()
    >>> bro.open('http://google.com')
    >>> button = bro.xpath('//button')[0]
    >>> bro.click(button)
    >>> bro.save_screenshot('test.png')
    >>> bro.quit()

Installation
------------

.. code:: shell

    $ pip install -U .


