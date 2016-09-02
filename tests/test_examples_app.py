# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Test example app."""

import json
import os
import signal
import subprocess
import time

import pytest


@pytest.yield_fixture
def example_app():
    """Example app fixture."""
    current_dir = os.getcwd()
    # go to example directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exampleappdir = os.path.join(project_dir, 'examples')
    os.chdir(exampleappdir)
    # setup example
    cmd = './app-setup.sh'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    # Starting example web app
    cmd = 'FLASK_APP=app.py flask run --debugger -p 5000'
    webapp = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              preexec_fn=os.setsid, shell=True)
    time.sleep(20)
    # return webapp
    yield webapp
    # stop server
    os.killpg(webapp.pid, signal.SIGTERM)
    # tear down example app
    cmd = './app-teardown.sh'
    subprocess.call(cmd, shell=True)
    # return to the original directory
    os.chdir(current_dir)


def test_example_app(example_app):
    """Test example app."""
    # load fixtures
    cmd = 'FLASK_APP=app.py flask fixtures records'
    exit_status = subprocess.call(cmd, shell=True)
    assert exit_status == 0
    time.sleep(7)
    # Testing record retrieval via web
    cmd = 'curl http://127.0.0.1:5000/records/1'
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert output['id'] == 1
    assert output['metadata']['control_number'] == '1'
    assert output['metadata']['description'] == \
        "This is an awesome description"
    assert output['metadata']['title'] == "Registered"

    # Testing record retrieval via web with query
    cmd = ('curl http://127.0.0.1:5000/records/'
           '?size=3&page=3&q=awesome&sort=-control_number')
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert len(output['hits']['hits']) == 3

    # Testing view options retrieval via web
    cmd = 'curl http://127.0.0.1:5000/records/_options'
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert len(output['sort_fields']) == 2
    for sort_field in output['sort_fields']:
        if 'title' in sort_field:
            assert sort_field['title']['default_order'] == 'asc'
            assert sort_field['title']['title'] == 'Title'
        if 'control_number' in sort_field:
            assert sort_field['control_number']['default_order'] == 'asc'
            assert sort_field['control_number']['title'] == 'Record identifier'

    # Testing suggest retrieval via web
    cmd = 'curl http://127.0.0.1:5000/records/_suggest?title-complete=Reg'
    output = json.loads(
        subprocess.check_output(cmd, shell=True).decode("utf-8")
    )
    assert output['title-complete'][0]['text'] == 'Reg'
