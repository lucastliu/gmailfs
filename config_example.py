import configparser



# Make an ini config file
config = configparser.ConfigParser()

config['EXAMPLE'] = {'example': '45'}

config['GMAIL'] = {'historyid': '3312',
                   'emailsperfolder': '50',
                   'enablequickfeatures': 'True'}

with open('config.ini', 'w') as configfile:
    config.write(configfile)

# read it

config.sections()
config.read('config.ini')

for key in config['GMAIL']:
    print(key)

# change it

config['EXAMPLE']['example'] = '10'
with open('config.ini', 'w') as configfile:
    config.write(configfile)
