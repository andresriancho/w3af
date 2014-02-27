"""
file_utils.py

Copyright 2008 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import string
import datetime
import os

from git import Repo

ALLOWED = string.digits + string.letters + '/.-_'


def replace_file_special_chars(filename_path):
    """This is a *very* incomplete function which I added to fix a bug:
    http://sourceforge.net/apps/trac/w3af/ticket/173308

    And after realizing that it was very hard to perform a replace
    that worked for all platforms and when the thing to sanitize was a
    path+filename and not only a filename."""
    return filename_path.replace(':', '_')

def days_since_file_update(filename, days):
    """
    :return: True if the filename was updated earlier than @days before today
    """
    time_delta_days = get_days_since_file_update(filename)
    return time_delta_days > days

def get_days_since_file_update(filename):
    """
    :return: The days since the last update 
    """
    repo = Repo(".")

    # Note that before I used repo.head.commit.iter_parents , but that had
    # the side-effect of skipping the first commit, which is exactly the one
    # I need!
    commits_iter = repo.head.commit.iter_items(repo, repo.head, paths=filename)
    
    for c in commits_iter:
        
        last_commit_time = datetime.datetime.fromtimestamp(c.authored_date)
        last_commit_date = last_commit_time.date()
                
        today_date = datetime.date.today()
    
        time_delta = today_date - last_commit_date
        
        return time_delta.days
    
    raise ValueError('"%s" is not in tracked by this repository.' % filename)
    
def days_since_newest_file_update(path):
    """
    :param path: The path to analyze
    :return: The days since the the latest update to the newest file in a path
    """
    days = 365
    
    for item in os.listdir(path):
        
        full_path = os.path.join(path, item)
        
        try:
            if os.path.isfile(full_path):            
                last_updated = get_days_since_file_update(full_path)
            else:
                last_updated = days_since_newest_file_update(full_path)
        except ValueError:
            last_updated = days
        
        if last_updated < days:
            days = last_updated
        
    return days