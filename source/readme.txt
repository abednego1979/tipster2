rm -rf tipster/
git clone https://github.com/abednego1979/tipster.git
sudo python tools.py
cd tipster
git add .
git commit -m 'patch0413'
git push -u origin master
cd ..

view remote code:
git remote -v

get code from remote
git fetch origin master

compare different between local and remote
git log -p master.. origin/master

merge download code to local
git merge origin/master