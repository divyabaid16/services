# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os.path

import responses
from parsepatch.patch import Patch


def test_mozreview():
    '''
    Test a mozreview revision
    '''
    from shipit_static_analysis.revisions import MozReviewRevision

    r = MozReviewRevision('308c22e7899048467002de4ffb126cac0875c994:164530:7')
    assert r.mercurial == '308c22e7899048467002de4ffb126cac0875c994'
    assert r.review_request_id == 164530
    assert r.diffset_revision == 7
    assert r.url == 'https://reviewboard.mozilla.org/r/164530/'
    assert r.build_diff_name() == '308c22e7-164530-7-clang-format.diff'


@responses.activate
def test_phabricator(mock_phabricator, mock_repository, mock_config):
    '''
    Test a phabricator revision
    '''
    from shipit_static_analysis.revisions import PhabricatorRevision
    from shipit_static_analysis.report.phabricator import PhabricatorReporter

    api = PhabricatorReporter({
        'url': 'http://phabricator.test/api/',
        'api_key': 'deadbeef',
    })

    r = PhabricatorRevision('51:PHID-DIFF-testABcd12', api)
    assert not hasattr(r, 'mercurial')
    assert r.diff_id == 42
    assert r.diff_phid == 'PHID-DIFF-testABcd12'
    assert r.url == 'https://phabricator.test/PHID-DIFF-testABcd12/'
    assert r.build_diff_name() == 'PHID-DIFF-testABcd12-clang-format.diff'
    assert r.id == 51  # revision

    # Check test.txt content
    test_txt = os.path.join(mock_config.repo_dir, 'test.txt')
    assert open(test_txt).read() == 'Hello World\n'

    # Load full patch
    assert r.patch is None
    r.apply(mock_repository)
    assert r.patch is not None
    assert isinstance(r.patch, str)
    assert len(r.patch.split('\n')) == 7
    patch = Patch.parse_patch(r.patch)
    assert patch == {
        'test.txt': {
            'touched': [],
            'deleted': [],
            'added': [2],
            'new': False
        }
    }

    # Check file is updated
    assert open(test_txt).read() == 'Hello World\nSecond line\n'


def test_clang_files(mock_revision):
    '''
    Test clang files detection
    '''
    assert mock_revision.files == []
    assert not mock_revision.has_clang_files

    mock_revision.files = ['test.cpp', 'test.h']
    assert mock_revision.has_clang_files

    mock_revision.files = ['test.py', 'test.js']
    assert not mock_revision.has_clang_files

    mock_revision.files = ['test.cpp', 'test.js', 'xxx.txt']
    assert mock_revision.has_clang_files

    mock_revision.files = ['test.h', 'test.js', 'xxx.txt']
    assert mock_revision.has_clang_files
