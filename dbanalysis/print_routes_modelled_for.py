import json
routes = json.loads(open('resources/trimmed_routes.json','r').read())
for route in routes:

    for v_num,variation in enumerate(routes[route]):

        f = open('routes_modelled_for.txt','a')
        f.write(route + '_' + str(v_num) + ' Towards ' + str(variation[0]) + '\n')
        f.close()
