#  Copyright  2020 Alexis Lopez Zubieta
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

import fnmatch
import glob
import logging
import os
import pathlib
import shutil

from appimagebuilder.modules.deploy.files.shared_object_dependencies_resolver import (
    SharedObjectDependenciesResolver,
)
from appimagebuilder.utils import elf


class FileDeploy:
    """
    Deploy helper that uses the PT_NEEDED entries to resolve dependencies between binaries
    """

    listings = {
        "graphics": [
            "**/libEGL.so*",
            "**/libGL.so*",
            "**/libGLX_mesa.so*",
            "**/libX11-xcb.so*",
            "**/libX11.so",
            "**/libdrm.so*",
            "**/libdrm_*",
            "**/libxcb-glx.so*",
            "**/libxcb-render.so*",
            "**/libxcb-shape.so*",
            "**/libxcb-shm.so*",
            "**/libxcb-xfixes.so*",
            "**/libxcb.so*",
        ],
        "glibc": [
            "**/libc-*.so",
            "**/libc.so*",
            "**/ld-*.so",
            "**/ld-linux-x86-64.so*",
            "etc/ld.so.conf.d/*",
            "**/libcrypt.so*",
            "**/libnss_compat-*.so",
            "**/libnss_nis.so*",
            "**/libmemusage.so*",
            "**/libpthread.so*",
            "**/libcrypt.so*",
            "**/libz.so*",
            "**/libpthread-*.so",
            "**/libutil.so*",
            "**/libnsl.so*",
            "**/libnss_nis-*.so",
            "**/libutil-*.so",
            "**/libdl-*.so",
            "**/libmvec-*.so",
            "**/libBrokenLocale.so*",
            "**/libnss_nisplus.so*",
            "**/libgcc_s.so*",
            "**/libnss_compat.so*",
            "**/libz.so*",
            "**/libthread_db-*.so",
            "**/libpcprofile.so",
            "**/librt.so*",
            "**/libnss_nisplus-*.so",
            "**/libnss_hesiod.so*",
            "**/libresolv.so*",
            "**/libBrokenLocale-*.so",
            "**/libnss_hesiod-*.so",
            "**/libSegFault.so",
            "**/libnss_files.so*",
            "**/libanl.so*",
            "**/librt-*.so",
            "**/libanl-*.so",
            "**/libresolv-*.so",
            "**/libm.so*",
            "**/libnss_files-*.so",
            "**/libthread_db.so*",
            "**/libdl.so*",
            "**/libnss_dns.so*",
            "**/libnsl-*.so",
            "**/libmvec.so*",
            "**/libnss_dns-*.so",
            "**/libm-*.so",
            "**/ld-linux-x86-64.so*",
            "**/gconv/*",
            "**/audit/*",
            "**/libstdc++.so*",
            "**/libstdcxx/*",
            "**/doc/zlib1g/*",
            "**/doc/libc6/*",
            "**/doc/gcc-10-base/*",
            "**/doc/libgcc-s1/*",
            "**/doc/libcrypt1/*",
            "**/doc/libstdc++6/*",
        ],
    }

    def __init__(self, app_dir: str):
        self.app_dir = pathlib.Path(app_dir).absolute()
        self.logger = logging.getLogger("FileDeploy")

    def deploy(self, paths: [str]):
        expanded_list = set()
        for path in paths:
            expanded_list = expanded_list.union(glob.glob(path, recursive=True))

        bundled_so_files = self._find_bundled_so_files()
        so_files_to_include, regular_files = self._filter_shared_object_files(
            expanded_list
        )
        all_so_files = list(bundled_so_files) + list(so_files_to_include)

        self.deploy_shared_objects(all_so_files)

        for path in regular_files:
            self._deploy_path(path)

    def _filter_shared_object_files(self, expanded_list):
        shared_object_files = []
        other_files = []
        for path in expanded_list:
            if elf.has_magic_bytes(path):
                shared_object_files.append(path)
            else:
                other_files.append(path)
        return shared_object_files, other_files

    def _deploy_path(self, path):
        if path.startswith(self.app_dir.__str__()):
            # don't redeploy
            return

        deploy_prefix = self._resolve_deploy_prefix(path)
        deploy_path = deploy_prefix / path.lstrip("/")

        self.logger.info("deploying %s" % path)
        if os.path.isfile(path):
            os.makedirs(os.path.dirname(deploy_path), exist_ok=True)
            shutil.copy2(path, deploy_path)
        elif os.path.isdir(path):
            os.makedirs(deploy_path, exist_ok=True)
        # special files (devices, sockets, etc.) get ignored here

    def _is_a_graphic_library(self, path):
        for pattern in self.listings["graphics"]:
            if fnmatch.fnmatch(path, pattern):
                return True

        return False

    def _resolve_deploy_prefix(self, path: str):
        for pattern in self.listings["glibc"]:
            if fnmatch.fnmatch(path, pattern):
                return self.app_dir / "opt/libc/"

        return self.app_dir

    def clean(self, paths: [str]):
        self.logger.info("Removing excluded files")
        base_paths = [
            pathlib.Path(self.app_dir),
            pathlib.Path(self.app_dir) / "opt" / "libc",
        ]

        for base_path in base_paths:
            for pattern in paths:
                try:
                    for match in base_path.glob(pattern):
                        self.logger.info(match.relative_to(self.app_dir))
                        if match.is_dir():
                            shutil.rmtree(match, ignore_errors=True)
                        else:
                            match.unlink()
                except FileNotFoundError:
                    # it's ok to ignore files that were already deleted
                    pass

    def deploy_shared_objects(self, so_files_to_include):
        self.logger.info("Resolving shared object files dependencies")
        ld_paths = set([os.path.dirname(file) for file in so_files_to_include])

        dependencies_resolve = SharedObjectDependenciesResolver(ld_paths)
        dependencies, duplicates = dependencies_resolve.get_dependencies_map(
            so_files_to_include
        )
        if duplicates:
            self.logger.info(
                "These files are required by other shared objects and can be safely omitted:"
            )
            for entry in duplicates:
                self.logger.info(f"\t{entry}")

        for file in dependencies:
            self._deploy_path(file)

        for file in so_files_to_include:
            self._deploy_path(file)

    def _find_bundled_so_files(self):
        so_files = set()
        for path in self.app_dir.glob("./**/*"):
            if path.is_file() and elf.has_magic_bytes(path):
                so_files.add(path.__str__())

        return so_files
