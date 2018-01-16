Deployment keys to perform **git push** deployment to the **DEV** environment.
The private is encrypted.


## Git push deploymement to the DEV

1. `push deploy` (where: deply = **ssh://ec2-user@dev.orcidhub.org.nz/~/repo.git**)
1. git **post-update** hook updated the site and restarts **docker-compose**:
```
#!/bin/sh
for r in "$@"; do
  case $r in
  refs/heads/*) git --work-tree=$HOME --git-dir=$HOME/repo.git checkout -f $(git rev-parse --symbolic --abbrev-ref $r)
  esac
done

cd $HOME
docker-compose restart
docker-compose logs --tail=60
```
