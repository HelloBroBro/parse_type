# -*- coding: UTF-8 -*-
"""
Tasks for releasing this project.

Normal steps::


    python setup.py sdist bdist_wheel

    twine register dist/{project}-{version}.tar.gz
    twine upload   dist/*

    twine upload  --skip-existing dist/*

    python setup.py upload
    # -- DEPRECATED: No longer supported -> Use RTD instead
    # -- DEPRECATED: python setup.py upload_docs

pypi repositories:

    * https://pypi.python.org/pypi
    * https://testpypi.python.org/pypi  (not working anymore)
    * https://test.pypi.org/legacy/     (not working anymore)

Configuration file for pypi repositories:

.. code-block:: init

    # -- FILE: $HOME/.pypirc
    [distutils]
    index-servers =
        pypi
        testpypi

    [pypi]
    # DEPRECATED: repository = https://pypi.python.org/pypi
    username = __USERNAME_HERE__
    password:

    [testpypi]
    # DEPRECATED: repository = https://test.pypi.org/legacy
    username = __USERNAME_HERE__
    password:

.. seealso::

    * https://packaging.python.org/
    * https://packaging.python.org/guides/
    * https://packaging.python.org/tutorials/distributing-packages/
"""

from __future__ import absolute_import, print_function
from invoke import Collection, task
from invoke_cleanup import path_glob
from .invoke_dry_run import DryRunContext


# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
@task
def checklist(ctx=None):    # pylint: disable=unused-argument
    """Checklist for releasing this project."""
    checklist_text = """PRE-RELEASE CHECKLIST:
[ ]  Everything is checked in
[ ]  All tests pass w/ tox

RELEASE CHECKLIST:
[{x1}]  Bump version to new-version by adding tag to the repository
[{x2}]  Build packages (sdist, bdist_wheel via prepare)
[{x3}]  Register and upload packages to testpypi repository (first)
[{x4}]    Verify release is OK and packages from testpypi are usable
[{x5}]  Register and upload packages to pypi repository
[{x6}]  Push last changes to Github repository

POST-RELEASE CHECKLIST:
[ ]  Bump version to new-develop-version by adding tag to the repository
[ ]  Adapt CHANGES (if necessary)
[ ]  Commit latest changes to Github repository
"""
    steps = dict(x1=None, x2=None, x3=None, x4=None, x5=None, x6=None)
    yesno_map = {True: "x", False: "_", None: " "}
    answers = {name: yesno_map[value]
               for name, value in steps.items()}
    print(checklist_text.format(**answers))


@task(name="bump_version")
def bump_version(ctx, new_version, dry_run=False):
    """Bump version (to prepare a new release)."""
    if not new_version.startswith("v"):
        new_version = "v{version}".format(version=new_version)

    if dry_run:
        ctx = DryRunContext(ctx)
    ctx.run("git tag {version}".format(version=new_version))


@task(name="build", aliases=["build_packages"])
def build_packages(ctx, hide=False):
    """Build packages for this release."""
    print("build_packages:")
    ctx.run("python -m build", echo=True, hide=hide)


@task
def prepare(ctx, new_version=None, hide=True,
            dry_run=False):
    """Prepare the release: bump version, build packages, ..."""
    if new_version is not None:
        bump_version(ctx, new_version, dry_run=dry_run)
    build_packages(ctx, hide=hide)
    packages = ensure_packages_exist(ctx, check_only=True)
    print_packages(packages)

# -- NOT-NEEDED:
# @task(name="register")
# def register_packages(ctx, repo=None, dry_run=False):
#     """Register release (packages) in artifact-store/repository."""
#     original_ctx = ctx
#     if repo is None:
#         repo = ctx.project.repo or "pypi"
#     if dry_run:
#         ctx = DryRunContext(ctx)

#     packages = ensure_packages_exist(original_ctx)
#     print_packages(packages)
#     for artifact in packages:
#         ctx.run("twine register --repository={repo} {artifact}".format(
#                 artifact=artifact, repo=repo))


@task
def upload(ctx, repo=None, repo_url=None, dry_run=False,
           skip_existing=False, verbose=False):
    """Upload release packages to repository (artifact-store)."""
    if repo is None:
        repo = ctx.project.repo or "pypi"
    if repo_url is None:
        repo_url = ctx.project.repo_url or None
    original_ctx = ctx
    if dry_run:
        ctx = DryRunContext(ctx)

    # -- OPTIONS:
    opts = []
    if repo_url:
        opts.append("--repository-url={0}".format(repo_url))
    elif repo:
        opts.append("--repository={0}".format(repo))
    if skip_existing:
        opts.append("--skip-existing")
    if verbose:
        opts.append("--verbose")

    packages = ensure_packages_exist(original_ctx)
    print_packages(packages)
    ctx.run("twine upload {opts} dist/*".format(opts=" ".join(opts)))

    # ctx.run("twine upload --repository={repo} dist/*".format(repo=repo))
    # 2018-05-05 WORK-AROUND for new https://pypi.org/:
    #   twine upload --repository-url=https://upload.pypi.org/legacy /dist/*
    # NOT-WORKING: repo_url = "https://upload.pypi.org/simple/"
    #
    # ctx.run("twine upload --repository-url={repo_url} {opts} dist/*".format(
    #    repo_url=repo_url, opts=" ".join(opts)))
    # ctx.run("twine upload --repository={repo} {opts} dist/*".format(
    #         repo=repo, opts=" ".join(opts)))


# -- DEPRECATED: Use RTD instead
# @task(name="upload_docs")
# def upload_docs(ctx, repo=None, dry_run=False):
#     """Upload and publish docs.
#
#     NOTE: Docs are built first.
#     """
#     if repo is None:
#         repo = ctx.project.repo or "pypi"
#     if dry_run:
#         ctx = DryRunContext(ctx)
#
#     ctx.run("python setup.py upload_docs")
#
# -----------------------------------------------------------------------------
# TASK HELPERS:
# -----------------------------------------------------------------------------
def print_packages(packages):
    print("PACKAGES[%d]:" % len(packages))
    for package in packages:
        package_size = package.stat().st_size
        package_time = package.stat().st_mtime
        print("  - %s  (size=%s)" % (package, package_size))


def ensure_packages_exist(ctx, pattern=None, check_only=False):
    if pattern is None:
        project_name = ctx.project.name
        project_prefix = project_name.replace("_", "-").split("-")[0]
        pattern = "dist/%s*" % project_prefix

    packages = list(path_glob(pattern, current_dir="."))
    if not packages:
        if check_only:
            message = "No artifacts found: pattern=%s" % pattern
            raise RuntimeError(message)
        else:
            # -- RECURSIVE-SELF-CALL: Once
            print("NO-PACKAGES-FOUND: Build packages first ...")
            build_packages(ctx, hide=True)
            packages = ensure_packages_exist(ctx, pattern,
                                             check_only=True)
    return packages


# -----------------------------------------------------------------------------
# TASK CONFIGURATION:
# -----------------------------------------------------------------------------
# DISABLED: register_packages
namespace = Collection(bump_version, checklist, prepare, build_packages, upload)
namespace.configure({
    "project": {
        "repo": "pypi",
        "repo_url": None,
    }
})
