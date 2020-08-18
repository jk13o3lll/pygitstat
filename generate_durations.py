import gitstat
import pygit2 as git
import sys, os, json, getpass, datetime
import dateutil.parser

# load configurations
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    # check json first
    config = json.load(f)
    assert ('title' in config and 'subtitle' in config and 'note' in config and 
            'url' in config and 'clone' in config and 'repository' in config and 
            'html' in config and 'export' in config and 'weights' in config and
            'query type' in config and 'queries' in config and 'authors' in config), 'Some settings in config file are missing.'
            # 'pubkey', 'privkey', 'fake commits', 'diary', 'author commits' are optional
    assert config['query type'] == 'track', 'Wrong query type'
    # set credentials
    credentials = None
    if 'pubkey' in config and 'privkey' in config:
        if os.path.exists(config['pubkey']) and os.path.exists(config['privkey']):
            username = 'git'
            pubkey = config['pubkey']
            privkey = config['privkey']
            passphrase = ''
            credentials = git.Keypair(username, pubkey, privkey, passphrase)
        else:
            print('File for pubkey or privkey does not exist')
    if credentials is None: # use username & password
        username = input('Please input your user name: ')
        password = getpass.getpass('Please input your password: ')
        credentials = git.UserPass(username, password)
        # pygit2 for windows could only use UserPass? cannot use SSH? (allowed = 1)
    callbacks = git.RemoteCallbacks(credentials=credentials)
    # get repo (clone if needed)
    if not os.path.exists(config['repository']):
        # path = os.path.dirname(config['repository'])
        path = config['repository']
        gitstat.clone(config['clone'], path, callbacks=callbacks)
    repo = git.Repository(config['repository'])
    # update
    gitstat.pull(repo, callbacks=callbacks)
    # load from json
    title = config['title']
    weights = config['weights']
    query_name = [query['name'] for query in config['queries']]
    durations = [(dateutil.parser.isoparse(query['since']), dateutil.parser.isoparse(query['until'])) for query in config['queries']]
    authors = [gitstat.Author(info, repo) for info in config['authors']]
    fake_commits = set(repo[rev].id for rev in config['fake commits']) if 'fake commits' in config else set()

# # generate statistics
commits = [commit for commit in repo.walk(repo.head.target)]
print('Totol number of commits:', len(commits))
for author in authors:
    print('Author:', author.name)
    for iquery, (since, until) in enumerate(durations):
        author.generate_stats(repo, commits, since, until, fake_commits, iquery)
    author.get_summary()
    author.get_summary_duration(durations)
    # author.check_diary(repo_dir, durations, check_file=True, check_content=True)
    print('  Total:')
    print('    NC: %d, L+: %d, L-: %d, W+: %d, W-: %d' % (
        author.n_commits,
        author.summary.lines_inserted, author.summary.lines_deleted,
        author.summary.words_inserted, author.summary.words_deleted))
    print('  Durations:')
    for iquery, stat in enumerate(author.summary_duration):
        print('    Query %d: L+: %d, L-: %d, W+: %d, W-: %d' %
            (iquery, stat.lines_inserted, stat.lines_deleted, stat.words_inserted, stat.words_deleted))
    

# generate html
# check html folder
out = config['html']
filename, fileext = os.path.splitext(out)
out_tmp = filename + '_tmp' + ext


# check time
tnow = datetime.now()
tnow_str = tnow.strftime
export_name = tnow.str