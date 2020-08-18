import os
import re # regular expression
import pygit2 as git
from datetime import datetime, timezone, timedelta
import dateutil.parser

# definition of file extensions (use set)
# ambiguous: 'ipynb', '.tex', '.bib', '.htm', '.html', ''
FILEEXT_TEXT = {'.md', '.txt', '.tex', ''}
FILEEXT_CODE = {'.m', '.py', '.h', '.c', '.hpp', '.cpp', 'java', '.jl', '.js', '.htm', '.html'}
FILEEXT_DATA = {'.mat', '.csv', '.dat', '.json', '.xml', '.drawio', '.bib'}
FILEEXT_BINARY = {'.mlx', '.exe', '.ipynb'}
FILEEXT_FIGURE_VECTOR = {'.pdf', '.eps', '.svg'}
FILEEXT_FIGURE_BITMAP_LOSSLESS = {'.png', '.tif', '.tiff'}
FILEEXT_FIGURE_BITMAP_LOSSY = {'.jpg', '.jpeg', '.bmp'}

# definition of a word
PATTERN_WORD = re.compile('(\S+)')

# definition of scores
EQUIVWORDS_FIGURE_VECTOR = 100
EQUIVWORDS_FIGURE_BITMAP_LOSSLESS = 50
EQUIVWORDS_FIGURE_BITMAP_LOSSY = 25
EQUIVWORDS_BIB_MAX = 100 # upper bound every time

def clone(url, path, callbacks=None):
    '''Clone from the repository.

    Example:
        ret = clone('https://..../.../xxx.git', '.../Repositories', callbacks=callbacks)

    Args:
        url (str): URL of the repository
        path (str): Local path to clone into
        callbacks (pygit2.RemoteCallbacks): Callback for credentials

    Returns:
        ret (bool): True for success, False otherwise.
    '''
    if not os.path.exists(path):
        print('Clone from %s to %s ...' % (url, path), end='')
        repo = git.clone_repository(url, path, callbacks=callbacks)
        if repo is None:    print('failed.');   return False
        else:               print('done.');     return True
    else:
        print('The repository has already existed.')
        return True
    
def pull(repo, remote_name='origin', branch='master', callbacks=None):
    '''Pull from the repository.

    Modified based on: https://github.com/MichaelBoselowitz/pygit2-examples/blob/master/examples.py

    Example:
        ret = pull(repo, callbacks=callbacks)

    Args:
        repo (pygit2.Repository): Repository object
        remote_name (str): Remote name
        callbacks (pygit2.RemoteCallbacks): Callback for credentials
    
    Returns:
        ret (bool): True for success, False otherwise.
    '''
    print('Pull to %s ...' % (repo.path), end='')
    for remote in repo.remotes:
        if remote.name == remote_name:
            remote.fetch(callbacks=callbacks) # fetch to the remote first
            remote_master_id = repo.lookup_reference('refs/remotes/origin/%s' % (branch)).target # find the branch
            merge_result, _ = repo.merge_analysis(remote_master_id) # auto merge
            if merge_result & git.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                print('up to date')
                return True
            elif merge_result & git.GIT_MERGE_ANALYSIS_FASTFORWARD:
                print('fast forward')
                # update the reference
                repo.checkout_tree(repo.get(remote_master_id))
                repo.lookup_reference('refs/heads/master').set_target(remote_master_id)
                repo.head.set_target(remote_master_id)
                return True
            elif merge_result & git.GIT_MERGE_NORMAL:
                print('normal merge')
                # merge
                repo.merge(remote_master_id)
                if repo.index.conflicts is not None:
                    print(repo.index.conflicts)
                    raise AssertionError('Conflicts in merge')
                # commit
                user = repo.default_signature
                tree = repo.index.write_tree()
                commit = repo.create_commit('HEAD', user, user, 'Automerge by gitstat', tree, [repo.head.target, remote_master_id])
                repo.state_cleanup()
                return True
            else:
                raise AssertionError('Unknown merge analysis result')
    else:
        printf('failed')
        return False

class Stat:
    def __init__(self, iquery, lines_inserted, lines_deleted, words_inserted, words_deleted):
        self.iquery = iquery # by which query
        self.lines_inserted = lines_inserted
        self.lines_deleted = lines_deleted
        self.words_inserted = words_inserted
        self.words_deleted = words_deleted
    
    def __iadd__(self, r):
        self.iquery = -1 # -1 if from addition
        self.lines_inserted += r.lines_inserted
        self.lines_deleted += r.lines_deleted
        self.words_inserted += r.words_inserted
        self.words_deleted += r.words_deleted
        return self

class FileStat:
    '''Statistics of a file

    .....

    TODO: deal with renaming
    '''
    def __init__(self, filepath):
        self.stats = list() # list of Stat (several stats from multiple queries)
        self.filepath = filepath # use filepath as key
        # ensure criteria for scoring
        self.fileext = os.path.splitext(filepath)[1].lower() # fileext always case insensitive
        if self.fileext in FILEEXT_TEXT:                        self.criteria = 0
        elif self.fileext in FILEEXT_CODE:                      self.criteria = 1
        elif self.fileext in FILEEXT_FIGURE_VECTOR:             self.criteria = 10
        elif self.fileext in FILEEXT_FIGURE_BITMAP_LOSSLESS:    self.criteria = 11
        elif self.fileext in FILEEXT_FIGURE_BITMAP_LOSSY:       self.criteria = 12
        else:                                                   self.criteria = -1
        
    def parse_append(self, iquery, patch_hunks, patch_status):
        '''Parse a patch in diff (in one commit), and append the stat'''
        if self.criteria == 0 or self.criteria == 1:
            lines_inserted, lines_deleted, words_inserted, words_deleted = 0, 0, 0, 0
            for hunk in patch_hunks:
                for line in hunk.lines:
                    words_diff = len(re.findall(PATTERN_WORD, line.content))
                    if words_diff == 0:         continue # exclude empty line, whitespace change, single linebreak
                    if line.origin == '+':      lines_inserted += 1; words_inserted += words_diff
                    elif line.origin == '-':    lines_deleted += 1;  words_deleted += words_diff
            if self.fileext == '.bib':
                lines_inserted, lines_deleted, words_deleted = 0, 0, 0
                if words_inserted > EQUIVWORDS_BIB_MAX: words_inserted = EQUIVWORDS_BIB_MAX
        elif self.criteria == 10:
            lines_inserted, lines_deleted, words_inserted, words_deleted = (0, 0, 0, EQUIVWORDS_FIGURE_VECTOR) if patch_status == 2 else (0, 0, 0, 0) # deleeted; added or modified
        elif self.criteria == 11:
            lines_inserted, lines_deleted, words_inserted, words_deleted = (0, 0, 0, EQUIVWORDS_FIGURE_BITMAP_LOSSLESS) if patch_status == 2 else (0, 0, 0, 0)
        elif self.critera == 12:
            lines_inserted, lines_deleted, words_inserted, words_deleted = (0, 0, 0, EQUIVWORDS_FIGURE_BITMAP_LOSSY) if patch_status == 2 else (0, 0, 0, 0)
        else:
            lines_inserted, lines_deleted, words_inserted, words_deleted = 0, 0, 0, 0
        # append data
        self.stats.append(Stat(iquery, lines_inserted, lines_deleted, words_inserted, words_deleted))

def _make_commit_filter(emails, since, until, fake_commits):
    '''Create filter function to filter out invalid commits
    '''
    def is_valid_commit(commit):
        t = datetime.fromtimestamp(float(commit.commit_time), timezone(timedelta(minutes=commit.commit_time_offset)))
        return (len(commit.parents) == 1 and        # non-merge
                t > since and t < until and         # within duration
                commit.id not in fake_commits and   # not fake commit (set)
                commit.committer.email in emails)   # is author (set)
    return is_valid_commit

class Author:
    def __init__(self, info, case_sensitive=True):
        self.name = info['name']
        self.emails = set(info['emails'])
        self.labels = info['labels']
        self.diary = info['diary'] if 'diary' in info else None
        # statistics
        self.case_sensitive = case_sensitive # whether key to files[] case-sensitive
        self.files = dict() # dictionary of FileStat
        self.summary = None
        self.summary_duration = None # list of Stat
        self.n_commits = 0 # to avoid count repeat commits for different files
        self.queries_with_commits = 0
        self.has_diary = None

    def generate_stats(self, repo, commits, since, until, fake_commits, iquery=0):
        '''Generate statistics of all the files in the commits of the author

        .....

        Args:
            repo (pygit2.Repository):
            commits (list(pygit2.Object)): (commits = [commit for repo.walk(repo.head.target)])
            since (...):
            until (...):
            fake_commits (set(str)):
            iquery (int):

        Notes:
            ...
        '''
        # get stats of files
        commit_filter = _make_commit_filter(self.emails, since, until, fake_commits)
        filtered_commits = list(filter(commit_filter, commits))
        n_commits = len(filtered_commits)
        if n_commits == 0: return
        # has some commits
        self.n_commits += n_commits
        self.queries_with_commits += 1
        for commit in filtered_commits:
            diff = repo.diff(commit.parents[0], commit)
            for patch in diff:
                delta = patch.delta
                filepath = delta.new_file.path if self.case_sensitive else delta.new_files.path.lower()
                fileext = os.path.splitext(filepath)[1].lower() # fileext always case insensitvie
                if filepath not in self.files:
                    self.files[filepath] = FileStat(filepath)
                if delta.status > 0 and delta.status < 4: # add, delete, modify (including binary)
                    self.files[filepath].parse_append(iquery, patch.hunks, delta.status)

    def get_summary(self):
        # summary for total
        self.summary = Stat(-1, 0, 0, 0, 0)
        for filestat in self.files.values():
            for stat in filestat.stats:
                self.summary += stat
    def get_summary_duration(self, durations):
        # summary for each duration
        self.summary_duration = [Stat(-1, 0, 0, 0, 0)] * len(durations)
        for filestat in self.files.values():
            for stat in filestat.stats:
                self.summary_duration[stat.iquery] += stat
        return self.summary_duration

    def check_diary(self, root, durations, check_file=False, chekc_content=False):
        self.has_diary = [False] * len(durations)
        if self.diary is None:  print('No diary path'); return
        # check by commit to file
        if check_file:
            key = diary if self.case_sensitive else diary.lower()
            if key not in self.files:
                print('No commits to diary')
            else:
                for iq in [stat.iquery for stat in self.files[key]]:
                    self.has_diary[iq] = True
        # check by diary content, go through the diary to find datetime
        if check_content:
            filepath = os.path.join(root, self.diary)
            if not os.path.exists(filepath):
                print('No diary file')
            else:
                dates = []
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        if line.startswith('#'):
                            try: dates.append(dateutil.parser.parse(line, fuzzy=True).date())
                            except ValueError: pass # pass if cannot parse date correctly
                if len(dates) > 0:
                    duration_dates = ((d[0].date(), d[1].date()) for d in durations) # gen obj
                    for i, (since, until) in enumerate(duration_dates):
                        if any((date >= since and date <= util) for date in dates):
                            self.has_diary[i] = True
                else:
                    print('Cannot find any date in diary')

