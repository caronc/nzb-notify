pushjet |logo| (Python API)
=============================

.. |logo| image:: http://i.imgur.com/DayiPBl.png
    :align: middle

Welcome to ``pushjet``, Python's `Pushjet <https://pushjet.io/>`__ (`see the server on GitHub <https://github.com/Pushjet/Pushjet-Server-Api>`__) API. Pushjet lets you push notifications directly to your phone (among other things)! This module lets you do that pushing from Python! It's pretty sweet - it lets you do all sorts of cool things, like integrating notifications into your web app or notifying you when something goes on sale.

And yep, the module's just named ``pushjet``. Spiffy name, and surely not at all confusing. Probably. Hopefully. Maybe.

How to install
--------------

The module is `on GitHub <https://github.com/obskyr/pushjet-py>`__, and `it's also on PyPI <https://pypi.python.org/pypi/pushjet>`__! That means you can install it using `pip <https://pip.pypa.io/en/latest/installing/>`__. Simply run the following to install it:

.. code:: bash

    > pip install pushjet

Bam, you're ready to go. It's compatible with both Python 2 and 3, too - nice, huh?

How to use
----------

See the *Getting started* section of the `documentation <http://pushjet.readthedocs.io/>`__. Here's a little taste:

.. code:: python

    import pushjet
    import uuid

    service = pushjet.Service.create(
        "Open courses", # Name
        "http://example.com/university_icon.png" # Icon URL
    )
    device = pushjet.Device(uuid.uuid4())
    device.subscribe(service)
    service.send(
        "A spot is open for you in the competitive eating course!", # Message
        "Course open", # Title
        "http://example.com/courses/eating/competitive" # Link
    )
    for message in device.get_messages():
        print message.title
        print message.message
        print message.link

For information on all the properties of the classes, and on how to use custom API instances, once again see the `documentation <http://pushjet.readthedocs.io/>`__.

Contact
=======

If there's a feature you're missing or a bug you've found in ``pushjet``, `open an issue on GitHub <https://github.com/obskyr/pushjet-py/issues/new>`__. If you've got a question - or there's anything you'd like to talk about at all, really - you can reach me via:

* `Twitter (@obskyr) <https://twitter.com/obskyr>`__
* `E-mail <mailto:powpowd@gmail.com>`__

I usually answer much faster on Twitter. Thaaaat... should be all. I think. Unless I've forgotten something, which I don't think I have. I never *think* I have, though, and then sometimes I still have. Let's hope I haven't this time.

Enjoy!
