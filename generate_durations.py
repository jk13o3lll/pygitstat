#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import gitstat
import pygit2 as git
import sys, os, json, getpass, shutil
import dateutil.parser
from datetime import datetime

print(sys.argv[0], 'at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# load configurations
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    # check json first
    config = json.load(f)
    assert ('title' in config and 'subtitle' in config and 'note' in config and 
            'url' in config and 'clone' in config and 'repository' in config and 
            'html' in config and 'export' in config and 'weights' in config and
            'query type' in config and 'queries' in config and 'authors' in config), 'Some settings in config file are missing.'
            # 'pubkey', 'privkey', 'fake commits', 'diary', 'author commits' are optional
    assert config['query type'] == 'durations', 'Wrong query type'
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
    repo_dir = config['repository']
    if not os.path.exists(repo_dir):
        gitstat.clone(config['clone'], repo_dir, callbacks=callbacks)
    repo = git.Repository(repo_dir)
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
    author.check_diary(os.path.dirname(repo_dir), durations, check_file=True, check_content=True)
    # print('  Total:')
    # print('    NC: %d, L+: %d, L-: %d, W+: %d, W-: %d' % (author.n_commits,
    #     author.summary.lines_inserted, author.summary.lines_deleted,
    #     author.summary.words_inserted, author.summary.words_deleted))
    # print('  Durations:')
    # for iquery, stat in enumerate(author.summary_duration):
    #     print('    Query %d: L+: %d, L-: %d, W+: %d, W-: %d' %
    #         (iquery, stat.lines_inserted, stat.lines_deleted, stat.words_inserted, stat.words_deleted))
    print('  NC: %d, L+: %d, L-: %d, W+: %d, W-: %d' % (
        author.n_commits,
        author.summary.lines_inserted, author.summary.lines_deleted,
        author.summary.words_inserted, author.summary.words_deleted))

# generate html
out = config['html']
filename, fileext = os.path.splitext(out)
out_tmp = filename + '_tmp' + fileext
# check html folder
dir = os.path.dirname(out)
if not os.path.exists(dir):
    os.makedirs(dir)
# check time
tnow = datetime.now()
tnow_str = tnow.strftime('%Y-%m-%d %H:%M:%S')
export_name = tnow.strftime('%Y%m%d_%H%M%S_') + config['export']
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
    f.write(
        '<table id="statistics" class="display">'
            '<thead><tr>' # table header'
                '<th></th>' # column for expand / collapse icon
                '<th>Authors</th>'
                '<th>Semester</th>'
    )
    for name in query_name:
        f.write('<th>{name}</th>'.format(name=name))
    f.write(
                '<th>Fake commits</th>'
                '<th>Net<br>lines count</th>'
                '<th>Net<br>words count</th>'
                '<th>Weeks<br>with commits</th>'
                '<th>Diary score</th>'
                '<th>Git score</th>'
            '</tr></thead>'
            '<tbody>' # table body
    )
    for author in authors:
        # hidden table for stats of files
        f.write(
            '<tr data-child-value="<table>' # subtable as child value
                '<thead><tr>' # subtable header
                    '<th>File name</th>'
                    '<th>Fake commits</th>'
                    '<th>Invalid commits</th>'
                    '<th>Valid commits</th>'
                    '<th>Lines inserted</th>'
                    '<th>Lines deleted</th>'
                    '<th>Words inserted</th>'
                    '<th>Words deleted</th>'
                '</tr></thead>'
                '<tbody>' # subtable content start
        )
        for fstat in author.files.values():
            tmp = sum(fstat.stats)
            f.write((
                '<tr>'
                '<td>{filepath}</td>'
                '<td>{n_fake_commits}</td>'
                '<td>{n_invalid_commits}</td>'
                '<td>{n_commits}</td>'
                '<td>{lines_inserted}</td>'
                '<td>{lines_deleted}</td>'
                '<td>{words_inserted}</td>'
                '<td>{words_deleted}</td>'
                '</tr>'
            ).format(
                filepath=fstat.filepath,
                n_fake_commits=0,
                n_invalid_commits=0,
                n_commits='--', # may calculate same commit
                lines_inserted=tmp.lines_inserted,
                lines_deleted=tmp.lines_deleted,
                words_inserted=tmp.words_inserted,
                words_deleted=tmp.words_deleted
            ))
        # statistics for the author
        f.write((
            '</tbody></table>">' # end of sub table
            '<td class="details-control"></td>' # button for expand subtable
            '<td>{name}</td>'
            '<td>{label}</td>'
        ).format(
            name=author.name,
            label=author.labels[0]
        ))
        for summary, has_diary in zip(author.summary_duration, author.has_diary):
            f.write(('<td{diary}>{data}</td>').format(
                diary='' if has_diary else ' class="no-diary"',
                data=summary.words_inserted+summary.words_deleted))
        f.write((
            '<td>{n_fake_commits}</td>'
            '<td>{net_lines_count}</td>'
            '<td>{net_words_count}</td>'
            '<td>{weeks_with_commits}</td>'
            '<td>{diary_score:.2f}</td>'
            '<td>{git_score:.2f}</td>'
            '</tr>'
        ).format(
            n_fake_commits=0,
            net_lines_count=author.summary.lines_inserted+author.summary.lines_deleted,
            net_words_count=author.summary.words_inserted+author.summary.words_deleted,
            weeks_with_commits=author.queries_with_commits,
            diary_score=0,
            git_score=0
        ))
    f.write(
            '</tbody>'
        '</table>'
    )
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
                        'iDisplayLength: 100,'
			'scrollX: true'
                    '}});'
                    # click for expand / collapse subtable
                    '$("#statistics").on("click", "td.details-control", function(){{'
                        'var tr = $(this).closest("tr");'
                        'var row = table.row(tr);'
                        'if(row.child.isShown()){{row.child.hide(); tr.removeClass("shown");}}'
                        'else{{row.child(tr.data("child-value")).show(); tr.addClass("shown");}}'
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
with open(out_tmp, 'r', encoding='utf-8') as src, open(out, 'w', encoding='utf-8') as dst:
    shutil.copyfileobj(src, dst)
