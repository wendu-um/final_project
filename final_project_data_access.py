import requests
import json
import sqlite3
import secret

CACHE_FILENAME='final_project.json'
key=secret.key
key_2=secret.key_2


class restaurant():
    def __init__(self,Id,name='N/A',rating='N/A',display_address='N/A',display_phone='N/A',review_count='N/A',price='N/A',distance='N/A',categories='N/A'):
        self.name=name
        self.rating=rating
        self.address=display_address
        self.phone=display_phone
        self.id=Id
        self.review_count=review_count
        self.price=price
        self.distance=distance
        self.categories=categories
        self.categories_str=','.join(categories)

    
    def info_to_save(self):
        return f'("{self.name}","[{self.categories_str}]","{self.id}","{self.address}","{self.phone}","{self.rating}","{self.review_count}","{self.price}")'


def create_table():
    connection=sqlite3.connect('final_project.sqlite')
    cursor=connection.cursor()
    query='''
    CREATE TABLE Restaurants(
    Name text,
    Categories text,
    Id text NOT NULL PRIMARY KEY,
    Address text,
    Phone text,
    Rating float,
    Review_Count int,
    Price text);'''
    cursor.execute(query)
    cursor.close()


def save_info_to_table(obj):
    connection=sqlite3.connect('final_project.sqlite')
    cursor=connection.cursor()
    info=obj.info_to_save()
    query=f'''
    INSERT INTO Restaurants
    VALUES {info};
    '''
    try:
        cursor.execute(query)
    except:
        pass
    connection.commit()
    cursor.close()


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Update current dictionary to cache file
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    try:
        fw = open(CACHE_FILENAME,"r")
        data=json.load(fw)
        fw.close()
        data.update(cache_dict)
        fw=open(CACHE_FILENAME,'w')
        fw.write(json.dumps(data))
        fw.close()
    except:
        dumped_json_cache = json.dumps(cache_dict)
        fw = open(CACHE_FILENAME,"w")
        fw.write(dumped_json_cache)
        fw.close()


def get_filtered_info(businesses):
    filtered_info = {key: businesses[key] for key in businesses.keys() 
                    & {'name','rating','display_phone','review_count','price','distance'}} 
    filtered_info['categories']=[y['title'] for y in businesses['categories']]
    filtered_info['display_address']=','.join(businesses['location']['display_address'])
    filtered_info['Id']=businesses['id']
    return filtered_info


def info_yelp(address):
    unique_key=str((address['lat'],address['lng']))
    cache=open_cache()
    if unique_key in cache:
        print ('Using Cache')
        restaurants_list=cache[unique_key]
    else:
        print ('Fetching')
        headers = {'Authorization':key_2}
        restaurants_list=[]
        i=0
        while True:
            param={'latitude':address['lat'],'longitude':address['lng'],'radius':40000,'limit':50,'categories':'restaurants','offset':i}
            output=requests.get('https://api.yelp.com/v3/businesses/search',headers=headers,params=param)
            i+=50
            try: 
                print ((output.json())['total'])
                result=output.json()['businesses']
                for businesses in result:
                    filtered_info=get_filtered_info(businesses)
                    restaurants_list.append(filtered_info)
            except:
                break
        save_cache({unique_key:restaurants_list})
    return [restaurant(**x) for x in restaurants_list] if len(restaurants_list)!=0 else None
            

def get_geometry(address):
    cache=open_cache()
    if address in cache:
        print ('Using Cache')
        return cache[address]
    else:
        print ('Fetching')
        param={'key':key,'address':address}
        output=requests.get('https://maps.googleapis.com/maps/api/geocode/json',param)
        geometry_dict={}
        if output.status_code==200 and len(output.json()['results'])!=0:
            result=output.json()['results'][0]
            geometry_dict['lat']=round(result['geometry']['location']['lat'],3)
            geometry_dict['lng']=round(result['geometry']['location']['lng'],3)
            geometry_dict['formatted_address']=result['formatted_address']
            save_cache({address:geometry_dict})
        else:
            print (f'{output.status_code} something wrong happened')
        return geometry_dict


if __name__ == "__main__":
    try:
        create_table()
    except:
        pass
    search_address= get_geometry('Ann Arbor')
    result_list=info_yelp(search_address)
    for x in result_list:
        save_info_to_table(x)