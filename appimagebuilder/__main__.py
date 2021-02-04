#!/usr/bin/env python3
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

import argparse
import logging
import os

from appimagebuilder import recipe
from appimagebuilder.builder.planner_v1 import PlannerV1
from appimagebuilder.generator.generator import RecipeGenerator
from appimagebuilder.tester import ExecutionTest


def __main__():
    parser = argparse.ArgumentParser(description="AppImage crafting tool")
    parser.add_argument(
        "--recipe",
        dest="recipe",
        default=os.path.join(os.getcwd(), "AppImageBuilder.yml"),
        help="recipe file path (default: $PWD/AppImageBuilder.yml)",
    )
    parser.add_argument(
        "--log", dest="loglevel", default="INFO", help="logging level (default: INFO)"
    )
    parser.add_argument(
        "--skip-script",
        dest="skip_script",
        action="store_true",
        help="Skip script execution",
    )
    parser.add_argument(
        "--skip-build",
        dest="skip_build",
        action="store_true",
        help="Skip AppDir building",
    )
    parser.add_argument(
        "--skip-tests",
        dest="skip_tests",
        action="store_true",
        help="Skip AppDir testing",
    )
    parser.add_argument(
        "--skip-appimage",
        dest="skip_appimage",
        action="store_true",
        help="Skip AppImage generation",
    )
    parser.add_argument(
        "--generate",
        dest="generate",
        action="store_true",
        help="Try to generate recipe from an AppDir",
    )

    args = parser.parse_args()
    logger = logging.getLogger("appimage-builder")
    numeric_level = getattr(logging, args.loglevel.upper())
    if not isinstance(numeric_level, int):
        logging.error("Invalid log level: %s" % args.loglevel)
    logging.basicConfig(level=numeric_level)

    if args.generate:
        generator = RecipeGenerator()
        generator.generate()
        exit(0)

    _run_build(args, logger)


def _run_build(args, logger):
    recipe_data = load_recipe(args.recipe)
    recipe_version = recipe_data.get_item("version")
    steps = []
    if recipe_version == 1:
        planner = PlannerV1(recipe_data)
        planner.skip_script = args.skip_script
        planner.skip_build = args.skip_build
        planner.skip_tests = args.skip_tests
        planner.skip_appimage = args.skip_appimage
        steps = planner.plan()
    else:
        logger.error("Unknown recipe version: %s" % recipe_version)
        logger.info("Please make sure you're using the latest appimage-builder version")
        exit(1)

    for step in steps:
        logger.info(step.title)
        step.run()


def _load_tests(recipe_data):
    test_cases = []

    appdir = recipe_data.get_item("AppDir/path", "AppDir")
    appdir = os.path.abspath(appdir)
    test_case_configs = recipe_data.get_item("AppDir/test", [])

    for name in test_case_configs:
        env = recipe_data.get_item("AppDir/test/%s/env" % name, [])
        if isinstance(env, dict):
            env = ["%s=%s" % (k, v) for k, v in env.items()]

        test = ExecutionTest(
            appdir=appdir,
            name=name,
            image=recipe_data.get_item("AppDir/test/%s/image" % name),
            command=recipe_data.get_item("AppDir/test/%s/command" % name),
            use_host_x=recipe_data.get_item("AppDir/test/%s/use_host_x" % name, False),
            env=env,
        )
        test_cases.append(test)

    return test_cases


def load_recipe(path):
    recipe_data = recipe.read_recipe(path=path)
    recipe_validator = recipe.Schema()
    recipe_validator.v1.validate(recipe_data)
    recipe_access = recipe.Recipe(recipe_data)

    return recipe_access


if __name__ == "__main__":
    # execute only if run as the entry point into the program
    __main__()
