#  Copyright  2021 Alexis Lopez Zubieta
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.

from .command import Command
from .apt_deploy import AptDeployCommand
from .create_appimage import CreateAppImageCommand
from .deploy_record import WriteDeployRecordCommand
from .file_deploy import FileDeployCommand
from .pacman_deploy import PacmanDeployCommand
from .run_shell_script import RunShellScriptCommand
from .run_test import RunTestCommand
from .setup_app_info import SetupAppInfoCommand
from .setup_runtime import SetupRuntimeCommand
from .setup_symlinks import SetupSymlinksCommand
