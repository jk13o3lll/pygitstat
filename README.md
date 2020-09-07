# gitstat
Python package to generate statistics from git.

## Dependencies

* Python3 (>=3.5) (sys, os, json, getpass, shutil, datetime, re, ...)
* Python: [pygit2](https://www.pygit2.org/), [python-dateutil](https://dateutil.readthedocs.io/en/stable/)
* Javascript: [DataTables](https://datatables.net/)

## Features

1. Navigation page (logo, title, multiple links)
   
 Width of screen < 800                |  Width of screen >= 800
 :-----------------------------------:|:-------------------------------------:
 ![](media/example_navigation_1.png)  |  ![](media/example_navigation_2.png)

2. Visualization of statistics
   
    * Show statistics in a table
    * Show details of committed file (click the button to expand or collapse)
    * Show whether the auther commits to diary
    * Copy, Export (excel, csv) (By DataTables)
    * Search, Sort, Pagination (By DataTables)
   
 For a long duration             | For multiple durations
 :------------------------------:|:------------------------------------:
 ![](media/example_total_1.png)  | ![](media/example_durations_1.png)
   
3. Generate statistics (Load settings from a json file)

    * Statistics (number of commits, lines inserted, lines deleted, words inserted, words deleted, ...)
    * Details of commits to each file
    * Exclude fake commits (use `"fake commits": ["commit_id1", ...]` to label them manually)
    * Consider specific commits as commits of an author (use `"his commits": ["commit_id1", ...]` to label them manually)
    * Scoring (according to the statistics and file extensions)
    * (only for `"query type": "durations"`) Diary check for every query (use `"diary": ["filepath_1", ...]` to set diary)
        * Whether there is any commit to specifc files
        * Whether there are some strings of date (within the durations) in specific files
   
## Usage

### **To use this tool**

```
git clone https://github.com/jk13o3lll/gitstat.git
pip install python-dateutil, pygit2
```

### **To generate statistics for a long duration**

```
python generate_total.py config_total.json
```

Format of `config_total.json` (Use `"pubkey"` and `"privkey"` to get authentication by ssh key.)

```
{
    "title": "Test -- total",
    "subtitle": "subtitle ...",
    "note": "Note that merges will not give unfair points.",
    "url": "https://github/jk13o3lll/pytorch-learning",
    "clone": "https://github.com/jk13o3lll/pytorch-learning.git", 
    "repository": "/home/jackwang/Repositories/pytorch-learning/.git",
    "pubkey": "/home/jackwang/.ssh/id_rsa.pub",
    "privkey": "/home/jackwang/.ssh/id_rsa",
    "html": "/home/jackwang/Repositories/gitstat/html/index_total.html",
    "export": "pytorch-learning",
    "weights": {
        "number of commits": 0.3, "lines inserted": 0.2, "lines deleted": 0.15, "words insreted": 0.2, "words deleted": 0.15
    },
    "query type": "total",
    "queries":[
        { "name": "Total", "since": "2015-09-08T00:00:00+08:00", "until": "2020-09-14T00:00:00+08:00" }
    ],
    "authors": [
        { "name": "Jack", "emails": ["ccwang.jack@gmail.com"], "labels": ["2019"] },
        { "name": "Others", "emails": ["noreply@github.com"], "labels": ["2019"] }
    ],
    "fake commits": [
        "6ec05deb10728f364"
    ]
}
```

### **To generate statistics for multiple durations**

```
python generate_durations.py config_durations.json
```

Format of `config_total.json` (If there is no `"pubkey"` or `"privkey"`, you will need to use username and password to log in.)

```
{
    "title": "Test -- durations",
    "subtitle": "subtitle ...",
    "note": "Note that merges will not give unfair points.",
    "url": "https://github/jk13o3lll/pytorch-learning",
    "clone": "https://github.com/jk13o3lll/pytorch-learning.git", 
    "repository": "/home/jackwang/Repositories/pytorch-learning/.git",
    "html": "/home/jackwang/Repositories/gitstat/html/index_duration.html",
    "export": "pytorch-learning",
    "weights": {
        "number of commits": 0.3, "lines inserted": 0.2, "lines deleted": 0.15, "words insreted": 0.2, "words deleted": 0.15
    },
    "query type": "durations",
    "queries":[
        { "name": "Week 1", "since": "2017-09-08T00:00:00+08:00", "until": "2018-09-14T00:00:00+08:00" },
        { "name": "Week 2", "since": "2018-09-08T00:00:00+08:00", "until": "2019-09-14T00:00:00+08:00" },
        { "name": "Week 3", "since": "2019-09-08T00:00:00+08:00", "until": "2020-09-14T00:00:00+08:00" }
    ],
    "authors": [
        { "name": "Jack", "emails": ["ccwang.jack@gmail.com"], "labels": ["2019"], "diary": ["Diary/my_diary.md"], "his commits": ["c32932b"] },
        { "name": "Others", "emails": ["noreply@github.com"], "labels": ["2019"], "diary": ["Diary/others_diary.md"] }
    ],
    "fake commits": [
        "6ec05deb10728f364"
    ]
}
```

### **To run this program automatically (for Linux)**

```
// add to crontab
crontab -e

// add the following line in crontab (run at 0:00 and 12:00 every day)
0 0,12 * * * python /aaa/bbb/generate_total.py /xxx/ooo/config_zzz.json >| /ppp/qqq/rrr.log 2>&1

```

### Suggest install

Ubuntu libssh2 only 1.18.0
CentOS 8 only libssh
Windows doesn't have libssh2

If use CentOS 8
1. Go to CentOS: https://www.centos.org/
1. Download DVD1.iso: http://centos.cs.nctu.edu.tw/8.2.2004/isos/x86_64/CentOS-8.2.2004-x86_64-dvd1.iso
1. Make boot USB: https://wiki.centos.org/HowTos/InstallFromUSBkey
1. Config static IP (optional): https://linuxconfig.org/rhel-8-configure-static-ip-address
1. Build SSH server: https://linuxconfig.org/how-to-install-start-and-connect-to-ssh-server-on-fedora-linux
1. Restrict IP of SSH server: https://www.cyberciti.biz/faq/match-address-sshd_config-allow-root-loginfrom-one_ip_address-on-linux-unix/?fbclid=IwAR17bt6Lvh-E9FF6iMjcj0geTNp4XowvzivDzySbwiOsMdKhoKZFkqLJpv4
1. Build Nginx server: https://www.footmark.info/linux/centos/centos8-installation-lemp/
1. If you change root or use virtual host, you should watch out mod and selinux: https://kknews.cc/zh-tw/code/kbj4nkq.html  https://www.nginx.com/blog/using-nginx-plus-with-selinux/?fbclid=IwAR17bt6Lvh-E9FF6iMjcj0geTNp4XowvzivDzySbwiOsMdKhoKZFkqLJpv4
1. Install development tools (GNU C, GIT, ...): https://linuxconfig.org/install-development-tools-on-redhat-8
1. Update packages (CMake in devtools, ...): https://blog.xuite.net/tolarku/blog/588694781-%5BCentOS+8%5D+%E5%A5%97%E4%BB%B6%E7%AE%A1%E7%90%86%E5%99%A8+DNF+-+Dandify+YUM
1. Install libgit2: https://centos.pkgs.org/8/centos-appstream-x86_64/libgit2-0.26.8-1.el8.x86_64.rpm.html
1. Install libssh2 1.9.0: https://centos.pkgs.org/8/epel-x86_64/libssh2-1.9.0-5.el8.x86_64.rpm.html
    wget https://download-ib01.fedoraproject.org/pub/epel/8/Everything/x86_64/Packages/l/libssh2-1.9.0-5.el8.x86_64.rpm
    rpm -Uvh libssh2-1.9.0-5.el8.x86_64.rpm
    sudo dnf install libssh2
1. Upgrade pip3: sudo pip3 install --upgrade pip
1. Build libgit2 from source: https://www.pygit2.org/install.html
    su
    pip3 install pygit2


* Install libgit2 from source (to ensure OPTION(USE_SSH) is on and compile correctly)?


## Contact

ccwang.jack@gmail.com
