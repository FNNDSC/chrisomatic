"""
Command-line interface to the `chrisomatic` program.
"""

import os
import logging
import chrisomatic

Gstr_title = r"""
   ________    ____  _________                       __  _     
  / ____/ /_  / __ \/  _/ ___/____  ____ ___  ____ _/ /_(_)____
 / /   / __ \/ /_/ // / \__ \/ __ \/ __ `__ \/ __ `/ __/ / ___/
/ /___/ / / / _, _// / ___/ / /_/ / / / / / / /_/ / /_/ / /__  
\____/_/ /_/_/ |_/___//____/\____/_/ /_/ /_/\__,_/\__/_/\___/  

"""
Gstr_title += (" " * 30) + "version " + chrisomatic.__version__ + "\n"


if "CHRISOMATIC_DEBUG" in os.environ:
    logging.basicConfig(level=logging.DEBUG)
