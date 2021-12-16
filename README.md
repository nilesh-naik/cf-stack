## What's this?
---
CloudFormation stack generated using Python

## Tools used
---
- Python
- [trophosphere](https://pypi.org/project/troposphere/)
- YAML

## How to use?
---
Install troposhere.
```
$ pip install troposphere
```
Run scripts to generate JSON templates.
```
$ python vpc.py
$ python security-groups.py
$ python db.py
$ python api-asg.py
$ python load-balancers.py
```
Create CloudFormation stack using above templates.