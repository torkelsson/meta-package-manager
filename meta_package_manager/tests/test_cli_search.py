# -*- coding: utf-8 -*-
#
# Copyright Kevin Deldycke <kevin@deldycke.com> and contributors.
# All Rights Reserved.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import pytest
import simplejson as json

from .conftest import MANAGER_IDS, unless_macos
from .test_cli import \
    test_manager_selection  # Run manager selection tests for this subcommand.
from .test_cli import check_manager_selection


@pytest.fixture
def subcommand():
    return 'search', 'abc'


def test_default_all_manager(invoke, subcommand):
    result = invoke(subcommand)
    assert result.exit_code == 0
    check_manager_selection(result.output)


@pytest.mark.parametrize('mid', MANAGER_IDS)
def test_single_manager(invoke, subcommand, mid):
    result = invoke('--manager', mid, subcommand)
    assert result.exit_code == 0
    check_manager_selection(result.output, {mid})


def test_json_parsing(invoke, subcommand):
    result = invoke('--output-format', 'json', subcommand)
    assert result.exit_code == 0
    data = json.loads(result.output)

    assert data
    assert isinstance(data, dict)
    assert set(data).issubset(MANAGER_IDS)

    for manager_id, info in data.items():
        assert isinstance(manager_id, str)
        assert isinstance(info, dict)

        assert isinstance(info['id'], str)
        assert isinstance(info['name'], str)

        assert set(info) == {'errors', 'id', 'name', 'packages'}

        assert isinstance(info['errors'], list)
        if info['errors']:
            assert set(map(type, info['errors'])) == {str}

        assert info['id'] == manager_id

        assert isinstance(info['packages'], list)
        for pkg in info['packages']:
            assert isinstance(pkg, dict)

            assert set(pkg) == {'id', 'latest_version', 'name'}

            assert isinstance(pkg['id'], str)
            if pkg['latest_version'] is not None:
                assert isinstance(pkg['latest_version'], str)
            assert isinstance(pkg['name'], str)


@unless_macos
def test_unicode_search(invoke):
    """ See #16. """
    result = invoke('--manager', 'cask', 'search', 'ubersicht')
    assert result.exit_code == 0
    assert "ubersicht" in result.output
    # XXX search command is not fetching yet detailed package infos like names.
    assert "Übersicht" not in result.output

    result = invoke('--manager', 'cask', 'search', 'Übersicht')
    assert result.exit_code == 0
    assert "ubersicht" in result.output
    assert "Übersicht" not in result.output


def test_exact_search_tokenizer(invoke):
    result = invoke('--manager', 'pip3', 'search', '--exact', 'sed')
    assert result.exit_code == 0
    assert "1 package total" in result.output
    assert " sed " in result.output

    for query in ['SED', 'SeD', 'sEd*', '*sED*', '_seD-@', '', '_']:
        result = invoke('--manager', 'pip3', 'search', '--exact', query)
        assert result.exit_code == 0
        assert "0 package total" in result.output
        assert "sed" not in result.output


def test_fuzzy_search_tokenizer(invoke):
    for query in ['', '_', '_seD-@']:
        result = invoke('--manager', 'pip3', 'search', query)
        assert result.exit_code == 0
        assert "0 package total" in result.output
        assert "sed" not in result.output

    for query in ['sed', 'SED', 'SeD', 'sEd*', '*sED*']:
        result = invoke('--manager', 'pip3', 'search', query)
        assert result.exit_code == 0
        assert "2 packages total" in result.output
        assert " sed " in result.output
        assert " SED-cli " in result.output


def test_extended_search_tokenizer(invoke):
    for query in ['', '_', '_seD-@']:
        result = invoke('--manager', 'pip3', 'search', '--extended', query)
        assert result.exit_code == 0
        assert "0 package total" in result.output
        assert "sed" not in result.output

    for query in ['sed', 'SED', 'SeD', 'sEd*', '*sED*']:
        result = invoke('--manager', 'pip3', 'search', '--extended', query)
        assert result.exit_code == 0
        assert "22 packages total" in result.output