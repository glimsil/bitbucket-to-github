import requests
import base64
import os
import json
from configparser import ConfigParser

config = ConfigParser()
config.read('config/config.txt')

def get_repos():
    clone_uris = []
    team_repos_uri = 'https://api.bitbucket.org/2.0/repositories/{team}?page={page}'
    page = 1
    while True:
        response = requests.get(team_repos_uri.replace('{team}', config['bitbucket']['team']).replace('{page}', str(page)), 
            headers={
            'Authorization' : 'Basic ' + str(base64.b64encode((config['bitbucket']['username'] 
            + ':' + config['bitbucket']['password']).encode('utf-8')),'utf-8')
            }
        )
        page += 1
        if(response.status_code == 200):
            body = response.json()
            for repo in body['values']:
                clone_uris.append(
                    {
                        'name' : repo['name'],
                        'description' : repo['description'],
                        'homepage' : repo['website'],
                        'clone': { 
                            'https':repo['links']['clone'][0]['href'], 
                            'ssh': repo['links']['clone'][1]['href']
                            },
                        'private' : repo['is_private'],
                        'has_issues' : repo['has_issues'],
                        'has_wiki' : repo['has_wiki'],
                        'links' : {
                            'pullrequests' : repo['links'].get('pullrequests', None), # só retorna com status OPEN
                            'issues' : repo['links'].get('issues', None),
                            'hooks' : repo['links'].get('hooks', None)
                        }
                    }
                    )
            if(body['pagelen'] > len(body['values'])):
                break
        else:
            break
    return clone_uris

def create_github_repo(repo):
    payload = {
        'name' : repo['name'], 
        'description': repo['description'],
        'homepage' : repo['homepage'],
        'private': repo['private'],
        'has_issues': repo['has_issues'],
        'has_wiki': repo['has_wiki']
    }
    response = requests.post('https://api.github.com/user/repos', 
        headers={
        'Authorization' : 'Basic ' + str(base64.b64encode((config['github']['username'] 
        + ':' + config['github']['password']).encode('utf-8')),'utf-8')
        },
        data=json.dumps(payload)
    )

def migrate_repos(repos):
    for repo in repos:
        repo_clone_uri = repo['clone']['https'].replace('@', ':'+config['bitbucket']['password']+'@')
        os.system('git clone --mirror ' + repo_clone_uri)
        create_github_repo(repo)
        new_repo_remote = 'git@github.com:{user}/{repo}.git'

        os.system('cd ' + repo['name'] + '.git;git remote set-url --push origin ' 
            + new_repo_remote.replace('{user}', config['github']['username'])
            .replace('{repo}', repo['name']) + ';git push --mirror')
        os.system('rm -rf ' + repo['name'] + '.git')

repos = get_repos()
migrate_repos(repos)