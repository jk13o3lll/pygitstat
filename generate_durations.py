import gitstat
import pygit2 as git
import sys, os, json, getpass, datetime, shutil
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

# generate statistics
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
out = config['html']
filename, fileext = os.path.splitext(out)
out_tmp = filename + '_tmp' + ext
# check html folder
dir = os.path.dirname(out)
if not os.path.exists(dir):
    os.mkdirs(dir)
# check time
tnow = datetime.now()
tnow_str = tnow.strftime('%Y-%m-%d %H:%M:%S')
export_name = tnow.str('%Y%m%d_%H%M%S_') + config['export']
# generate html
with open(out_tmp, 'w', encoding='utf-8') as f:
    # head
    f.write((
        '<!DOCTYPE html>'
        '<html>'
        '<head>'
            '<meta charset="utf-8"/>'
            '<title>{title}</title>'
            '<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.20/css/jquery.dataTables.min.css">'
            '<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/1.6.1/css/buttons.dataTables.min.css">'
            '<link rel="stylesheet" type="text/css" href="./gitstat_style.css">'
        '</head>'
        '<body>'
            '<header>'
                '<h1>{title}</h1>'
                '<p>Updated {tnow_str} from the git repository.</p>'
            '</header>'
            '<main>'
                '<h2>{subtitle}</h2>'
                '<p>{note}</p>'
    ).format(
        title=config['title'],
        tnow_str=tnow_str,
        subtitle=config['subtitle'],
        note=config['note']
    ))
    # table

    # footer
    f.write((
        '</main>'
            '<footer>'
                '<p>{footer}</p>'
            '</footer>'
            '<script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.3.1.min.js"></script>'
            '<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.10.20/js/jquery.dataTables.min.js"></script>'
            '<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/buttons/1.6.1/js/dataTables.buttons.min.js"></script>'
            '<script type="text/javascript" charset="utf8" src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.1.3/jszip.min.js"></script>'
            '<script type="text/javascript" charset="utf8" src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/pdfmake.min.js"></script>'
            '<script type="text/javascript" charset="utf8" src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/vfs_fonts.js"></script>'
            '<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/buttons/1.6.1/js/buttons.html5.min.js"></script>'
            '<script type="text/javascript" charset="utf8">'
                '$(document).ready(function(){{'
                    # apply datatable
                    'var table = $("#statistics").DataTable({{'
                        'dom: "Blfrtip",' # https://datatables.net/reference/option/dom
                        'buttons: ['
                            '"copyHtml5",'
                            '{{extend: "excelHtml5", title: "{export_name}"}},'
                            '{{extend: "csvHtml5", title: "{export_name}"}}'
                        '],'
                        'iDisplayLength: 100'
                    '}});'
                    # click for expand / collapse subtable
                    '$("#statistics").on("click", "td.details-control", function(){{'
                        'var tr = $(this).closest("tr");'
                        'var row = table.row(tr);'
                        'if(row.child.isShown()){{row.child.hide();tr.removeClass("shown");}}'
                        'else{{row.child(tr.data("child-value")).show();tr.addClass("shown");}}'
                    '}});'
                '}});'
            '</script>'
        '</body>'
        '</html>'
    ).format(
        footer='',
        export_name=export_name
    ))


    # copy to destination
    with open(out, 'w', encoding='utf-8') as dst:
        shutil.copyfileobj(f, dst)
