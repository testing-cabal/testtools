#!/usr/bin/python

"""Release testtools on Launchpad.

Steps:
 1. Make sure all "Fix committed" bugs are assigned to 'next'
 2. Rename 'next' to the new version
 3. Release the milestone
 4. Upload the tarball
 5. Create a new 'next' milestone
 6. Mark all "Fix committed" bugs in the milestone as "Fix released"

Assumes that NEWS is in the same directory, that the release sections are
underlined with '~' and the subsections are underlined with '-'.

Assumes that this file is in the top-level of a testtools tree that has
already had a tarball built and uploaded with 'python setup.py sdist upload
--sign'.
"""

from datetime import date
import logging
import os
import sys

from launchpadlib.launchpad import Launchpad
from launchpadlib import uris


APP_NAME = 'testtools-lp-release'
CACHE_DIR = os.path.expanduser('~/.launchpadlib/cache')
SERVICE_ROOT = uris.LPNET_SERVICE_ROOT

FIX_COMMITTED = u"Fix Committed"
FIX_RELEASED = u"Fix Released"

# Launchpad file type for a tarball upload.
CODE_RELEASE_TARBALL = 'Code Release Tarball'

PROJECT_NAME = 'testtools'
NEXT_MILESTONE_NAME = 'next'


def configure_logging():
    level = logging.DEBUG
    log = logging.getLogger(APP_NAME)
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log
log = configure_logging()


def get_path(relpath):
    """Get the absolute path for something relative to this file."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relpath))


def assign_fix_committed_to_next(testtools, next_milestone):
    """Find all 'Fix Committed' and make sure they are in 'next'."""
    fixed_bugs = list(testtools.searchTasks(status=FIX_COMMITTED))
    for task in fixed_bugs:
        log.debug("%s" % (task.title,))
        if task.milestone != next_milestone:
            task.milestone = next_milestone
            log.info("Re-assigning %s" % (task.title,))
            task.lp_save()


def rename_milestone(next_milestone, new_name):
    """Rename 'next_milestone' to 'new_name'."""
    next_milestone.name = new_name
    next_milestone.lp_save()


def get_release_notes_and_changelog(news_path):
    release_notes = []
    changelog = []
    state = None
    last_line = None

    def is_heading_marker(line, marker_char):
        return line and line == marker_char * len(line)

    with open(news_path, 'r') as news:
        for line in news:
            line = line.strip()
            if state is None:
                if is_heading_marker(line, '~'):
                    milestone_name = last_line
                    state = 'release-notes'
                else:
                    last_line = line
            elif state == 'title':
                # The line after the title is a heading marker line, so we
                # ignore it and change state. That which follows are the
                # release notes.
                state = 'release-notes'
            elif state == 'release-notes':
                if is_heading_marker(line, '-'):
                    state = 'changelog'
                    # Last line in the release notes is actually the first
                    # line of the changelog.
                    changelog = [release_notes.pop(), line]
                else:
                    release_notes.append(line)
            elif state == 'changelog':
                if is_heading_marker(line, '~'):
                    # Last line in changelog is actually the first line of the
                    # next section.
                    changelog.pop()
                    break
                else:
                    changelog.append(line)
            else:
                raise ValueError("Couldn't parse NEWS")
    release_notes = '\n'.join(release_notes).strip() + '\n'
    changelog = '\n'.join(changelog).strip() + '\n'
    return milestone_name, release_notes, changelog


def release_milestone(milestone, release_notes, changelog):
    date_released = date.today()
    return milestone.createProductRelease(
        date_released=date_released,
        changelog=changelog,
        release_notes=release_notes,
        )


def upload_tarball(release, tarball_path):
    with open(tarball_path) as tarball:
        tarball_content = tarball.read()
    sig_path = tarball_path + '.sig'
    with open(sig_path) as sig:
        sig_content = sig.read()
    tarball_name = os.path.basename(tarball_path)
    release.add_file(
        file_type=CODE_RELEASE_TARBALL,
        file_content=tarball_content, filename=tarball_name,
        signature_content=sig_content,
        signature_filename=sig_path,
        content_type="application/x-gzip; charset=binary")


def release_testtools(testtools, next_milestone):
    FOR_REAL = False
    assign_fix_committed_to_next(testtools, next_milestone)
    release_name, release_notes, changelog = get_release_notes_and_changelog(
        get_path('NEWS'))
    if FOR_REAL:
        rename_milestone(next_milestone, release_name)
        release = release_milestone(next_milestone)
        upload_tarball(
            release, get_path('dist/testtools-%s.tar.gz' % (release_name,)))
    else:
        print "Rename milestone to %s" % (release_name,)
        print "Upload tarball: dist/testtools-%s.tar.gz" % (release_name,)
        print 'Release notes: """%s"""' % (release_notes,)
        print 'Changelog: """\\\n%s"""' % (changelog,)

    # create milestone, 'next'
    # mark all fix committed as fix released


def main(args):
    launchpad = Launchpad.login_with(
        'jml-crit-bug', SERVICE_ROOT, CACHE_DIR)
    testtools = launchpad.projects[PROJECT_NAME]
    next_milestone = testtools.getMilestone(name=NEXT_MILESTONE_NAME)
    release_testtools(testtools, next_milestone)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
