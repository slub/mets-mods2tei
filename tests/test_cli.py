from click.testing import CliRunner
# -*- coding: utf-8 -*-

from mets_mods2tei import cli

def test_help():

    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert(result.exit_code == 0)

def test_failure():

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert(result.exit_code == 2)

def test_test_file():

    runner = CliRunner()
    result = runner.invoke(cli, ['tests/test_mets/test_mets.xml'])
    assert(result.exit_code == 0)
