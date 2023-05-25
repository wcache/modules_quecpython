
# import git
# print('git python version: ', git.__version__)


github_url = 'https://github.com/QuecPython/modules.git'
gitee_url = 'https://gitee.com/dustin-wei/modules.git'


# ------直接调用Git执行文件-----
# from git import Git
# g = git.Git()
# print('git version: ', g.version_info)
# print('git status: \n', g.execute('git status'))
# g(work_tree='/tmp').difftool()
# print('git log: \n', g.execute('git log'))
# print(g.reflog())
# g.rm('--cached', 'led.py')
# print(g.rm('--cached', '-f', '包管理器优化.txt'))
# g.clone(gitee_url)


# -----使用Repo管理仓库------
from git.repo import Repo
from pathlib import Path

# repo = Repo('C:/Users/dustin.wei/Desktop/test.git')
# new_repo = repo.clone('C:/Users/dustin.wei/Desktop/package_cmd/testdir')
# print('repo: ', repo)
# print('new_repo: ', new_repo)

origin_url = r'file:///C:\Users\dustin.wei\Desktop\test.git'
local_path = Path.cwd() / 'testdir'
# clone远程 Repo
# repo = Repo.clone_from(origin_url, str(local_path), recursive=True)
# clone远程 Git
# from git import Git
# g = Git('C:/Users/dustin.wei/Desktop/package_cmd/testdir')
# g.clone(origin_url, local_path)
# print(g.status())
# g.add('2.txt')
# g.rm('--cached', '2.txt')

repo = Repo(local_path)
# print('working_tree_dir: ', repo.working_tree_dir)
# print('active_branch: ', repo.active_branch)
# print('common_dir: ', repo.common_dir)
# print('bare: ', repo.bare)
# print('remotes: ', repo.remotes)
# print('references: ', repo.references)
# print('head: ', repo.head)
# print('heads: ', repo.heads)
# print('tags: ', repo.tags)
# print('tag: ', repo.tag('release/1.0'))
# print('index: ', repo.index)
# print('submodules: ', repo.submodules)
# print('submodule: ', repo.submodule('subtest'))
# subtest = repo.submodule('subtest')
# subtest.update()
# repo.submodule_update() # all
# repo.create_remote('origin', origin_url) # git remote add <origin> <url>
# repo.delete_remote(repo.remote('origin')) # git remote remove <origin>
# repo.create_tag('release/1.0')
# repo.delete_tag(repo.tag('release/1.0'))
# repo.create_head('NEW_HEAD') # 创建新分支
# repo.delete_head('NEW_HEAD', 'NEW_HEAD2') # 删除分支
# print('is_dirty: ', repo.is_dirty())
# print('tree: ', repo.tree())
# print('commits: ', [x for x in repo.iter_commits()])
# print('untracked_files: ', repo.untracked_files)
# repo.git.rm('--cached', '2.txt')
# repo.git.add('2.txt')
# print('current commit: ', repo.commit())
# repo.git.commit('-m', 'add 2.txt')
# repo.git.push('origin', 'master')
print(
    [branch.name for branch in repo.branches]
)
