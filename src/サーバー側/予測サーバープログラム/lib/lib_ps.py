#elastic.usernae
#elastic.password
#server.ip

def PS():
    file_path = "/opt/elastic_ps.txt"
    with open(file_path) as f:
        ps = f.read().splitlines()
    return ps
PS()