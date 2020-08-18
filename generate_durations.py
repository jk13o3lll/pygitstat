import gitstat
import pygit2 as git
import sys, os, json, getpass
import dateutil.parser

# load configurations
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    config = json.load(f)
    title = config['title']
    weights = config['weights']
    query_name = [query['name'] for query in config['queries']]
    durations = [(dateutil.parser.isoparse(query['since']), dateutil.parser.isoparse(query['until'])) for query in config['queries']]
    authors = [gitstat.Author(info) for info in config['authors']]
    repo = git.Repository(config['repository'])
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
    # update
    callbacks = git.RemoteCallbacks(credentials=credentials)
    gitstat.pull(repo, callbacks=callbacks)
    # get fake commit id
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
    print('  NC: %d, L+: %d, L-: %d, W+: %d, W-: %d' % (
        author.n_commits,
        author.summary.lines_inserted, author.summary.lines_deleted,
        author.summary.words_inserted, author.summary.words_deleted))

# generate html
