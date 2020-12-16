import requests
import json
import sqlite3
import secret
import plotly.graph_objs as go
import sys

CACHE_FILENAME='final_project.json'
key=secret.key
key_2=secret.key_2


class restaurant():
    '''infomation of a restaurant

    Instance Attributes
    -------------------
    categories: list of string 
        contains the categories the restaurant belongs to.
    name: string
        the name of the restaurant
    address: string
        the detailed address of the restaurant
    Id: string
        the yelp id of the restaurant, unique to each restaurant
    phone: string
        the phone of the restaurant
    review count: int
        number of review of the restaurant
    price: string
        price level of the restaurant, (e.g.'$','$$')
    rating: float
        average rating of the restaurant
    '''
    def __init__(self,Id,name='N/A',rating='N/A',display_address='N/A',display_phone='N/A',review_count='N/A',price='N/A',categories='N/A'):
        self.name=name
        self.rating=rating
        self.address=display_address
        self.phone=display_phone
        self.id=Id
        self.review_count=review_count
        self.price=price
        self.categories=categories
        self.categories_str=','.join(categories)

    
    def info_to_save(self):
        return f'("{self.name}","[{self.categories_str}]","{self.id}","{self.address}","{self.phone}","{self.rating}","{self.review_count}","{self.price}")'


class category():
    '''infomation of a category of restaurants

    Instance Attributes
    -------------------
    name: string
        the name of the category
    total_count: int
        sum of the review counts of all the restaurants belong to the category, used to calculate avg rating of the category
    total_rating: float
        sum of the review count * average rating of all the restaurants belong to the category, used to calculate avg rating of the category
    id_list: list
        list contains the id of all the restaurants belong to the category
    '''
    def __init__(self,name):
        self.name=name
        self.total_count=0
        self.total_rating=0
        self.id_list=[]

    def add_restaurant(self,rating,count,id):
        self.total_count+=count
        self.total_rating+=count*rating
        self.id_list.append(id)
    
    def avg_rating(self):
        return round(self.total_rating/self.total_count,2)

    def info(self):
        return f"{self.name} Average rating: {self.avg_rating}, {len(self.id_list)} restaurant {self.total_count} reviews in total"


def create_table():
    ''' Creat the restaurant table in database to store all the information of restaurants

    Parameters
    ----------
    None

    Returns
    -------
    None
    '''
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


def save_info_to_table(restaurant):
    ''' Save the attributes of a restaurant instance to the database

    Parameters
    ----------
    restaurant:
        A Restaurant Instance

    Returns
    -------
    None
    '''
    connection=sqlite3.connect('final_project.sqlite')
    cursor=connection.cursor()
    info=restaurant.info_to_save()
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
    ''' get data needed from the raw data obtained by yelp API
    
    Parameters
    ----------
    business: dict
        The raw data obtained by yelp API contains all infomation of a restaurant
    
    Returns
    -------
    filtered_info: dict
        The dictionary that contains the attributes to store in restaurant instance
        key:attributes (e.g:'name','id'), value:values of those attributes
        
    '''
    filtered_info = {key: businesses[key] for key in businesses.keys() 
                    & {'name','rating','display_phone','review_count','price'}} 
    filtered_info['categories']=[y['title'] for y in businesses['categories']]
    filtered_info['display_address']=','.join(businesses['location']['display_address'])
    filtered_info['Id']=businesses['id']
    return filtered_info


def info_yelp(address):
    ''' request yelp API to get infomation of all the restaurants within range of 10km to the input address
    
    Parameters
    ----------
    address: dict
        the dictionary contains the latitude and longitude of the address to search, 
        obtained by get_geometry() function
    
    Returns
    -------
    list of restaurants instances
        A list of restaurants instances that closed to the input address
        
    '''
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
            param={'latitude':address['lat'],'longitude':address['lng'],'radius':10000,'limit':50,'categories':'restaurants','offset':i}
            output=requests.get('https://api.yelp.com/v3/businesses/search',headers=headers,params=param)
            i+=50
            try: 
                result=output.json()['businesses']
                for businesses in result:
                    filtered_info=get_filtered_info(businesses)
                    restaurants_list.append(filtered_info)
            except:
                break
        save_cache({unique_key:restaurants_list})
    return [restaurant(**x) for x in restaurants_list] if len(restaurants_list)!=0 else None
            

def get_geometry(address):
    ''' Request the Google geocoding API to get the latitude and longitude of a address
    
    Parameters
    ----------
    address: string
        The string of input address
    
    Returns
    -------
    geometry_dict: dict
        The dictionary that contains the longitude and latitude of the input address
        
    '''
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


def classify_restaurants(result_list):
    ''' Classify a list of restaurant instances into different categories
    
    Parameters
    ----------
    result_list: list
        A list contains restaurant instances, obtained by info_yelp() function
    
    Returns
    -------
    category_list: list
        A list contains category instances related to the search

    '''
    category_list=[]
    exist_categories={}
    for restaurant in result_list:
        for c in restaurant.categories:
            if c not in exist_categories:
                exist_categories[c]=[restaurant]
            else:
                exist_categories[c].append(restaurant)
    for x in exist_categories:
        new_category=category(x)
        for restaurant in exist_categories[x]:
            new_category.add_restaurant(restaurant.rating,restaurant.review_count,restaurant.id)
        if new_category.total_count >=500:
            category_list.append(new_category) 
    category_list.sort(key=lambda x: x.total_count, reverse=True)
    return category_list
        
    
def info_of_category(category):
    ''' Get the attributes of all the restaurants belong to the input category instance from database,
        attributes includes Name, rating, review count and id
    
    Parameters
    ----------
    category: A category instance
    
    Returns
    -------
    result: list
        A list of tuples that contains the attributes, 
        each tuple contains attributes of a restaurant
        
    '''
    connection=sqlite3.connect('final_project.sqlite')
    cursor=connection.cursor()
    id_list=category.id_list
    query=f'''
    SELECT Name, Rating, Review_count,Id FROM Restaurants
    WHERE Id in {tuple(id_list)}
    ORDER BY Rating DESC;
    '''
    result = cursor.execute(query).fetchall()
    connection.close()
    return result


def info_of_restaurant(Id):
    ''' Get all attributes of certain restaurant from database,
        return a string
    
    Parameters
    ----------
    Id: string
        Id of the restaurant
    
    Returns
    -------
    string
        a string contains the infomation of the restaurant displayed to users
        
    '''
    connection=sqlite3.connect('final_project.sqlite')
    cursor=connection.cursor()
    query=f'''
    SELECT * FROM Restaurants
    WHERE Id = '{Id}';
    '''
    result = cursor.execute(query).fetchall()[0]
    connection.close()
    return f"Name:{result[0]}, Address:{result[3]}, Phone:{result[4]}, Rating:{result[5]}, Review Count:{result[6]}, Price:{result[7]}"


def print_figure_all_categories(category_list):
    ''' Generate a bar chart that displays the total review count and average rating of each category
    
    Parameters
    ----------
    category_list: list
        A list of categories obtained by classify_restaurants() function
    
    Returns
    -------
    None
        
    '''
    name=[]
    i=1
    for category in category_list:
        name.append(f"[{i}] {category.name}")
        i+=1
    avg_rating=[category.avg_rating() for category in category_list]
    review_count=[category.total_count for category in category_list]
    bar_data=[go.Bar(name='Review count',x=name,y=review_count,yaxis='y',offsetgroup=1,text=review_count,textposition='auto'),
            go.Bar(name='avg_rating',x=name,y=avg_rating,yaxis='y2',offsetgroup=2,text=avg_rating,textposition='auto')]
    layout={'yaxis': {'title': 'Review Count'},
            'yaxis2': {'title': 'Avg rating', 'overlaying': 'y', 'side': 'right'}}
    fig=go.Figure(data=bar_data,layout=layout)
    fig.update_layout(barmode='group')
    fig.show()


def print_figure_one_category(category):
    ''' Generate a bar chart that displays the review count and average rating of all restaurants belong to certain category
    
    Parameters
    ----------
    category: A category instance
    
    Returns
    -------
    None
        
    '''
    info=info_of_category(category)
    name=[]
    i=1
    for restaurant in info:
        name.append(f"[{i}] {restaurant[0]}")
        i+=1
    avg_rating=[restaurant[1] for restaurant in info]
    review_count=[restaurant[2] for restaurant in info]
    bar_data=[go.Bar(name='Review count',x=name,y=review_count,yaxis='y',offsetgroup=1,text=review_count,textposition='auto'),
            go.Bar(name='avg_rating',x=name,y=avg_rating,yaxis='y2',offsetgroup=2,text=avg_rating,textposition='auto')]
    layout={'yaxis': {'title': 'Review Count'},
            'yaxis2': {'title': 'Avg rating', 'overlaying': 'y', 'side': 'right'}}
    fig=go.Figure(data=bar_data,layout=layout)
    fig.update_layout(barmode='group')
    fig.show()


def enter_address():
    ''' Allow user to enter an address to search for closed restaurants,
        generate the bar chart that display info of the categories
    
    Parameters
    ----------
    None
    
    Returns
    -------
    category_list: list
        A list contains category instances related to the search address,
        obtained by classify_restaurants() function
        
    '''
    address=None
    while address==None:
        input_address=input('Please enter an address to search:')
        search_address=get_geometry(input_address)
        confirm=input(f"""The address to search is {search_address['formatted_address']}.
                        Press any key to continue, enter 'back' to enter a more detailed address,
                        enter 'exit' to exit the program""")
        if confirm=='exit':
            print ('bye')
            sys.exit()
        elif confirm !='back':
            address=search_address
    category_list=classify_restaurants(info_yelp(address))
    print_figure_all_categories(category_list)
    return category_list


def select_category(category_list):
    ''' Allow user to select a category from the list of categories related to the search,
        generate the bar chart displayed the info of restaurants under that category
    
    Parameters
    ----------
    category_list: list
        A list of category instance related to the search
    
    Returns
    -------
    info: list
        A list of tuples contains info of all the restaurant belongs to the selected categories,
        obtained by info_of_category() function
        
    '''
    category_selected=None
    while category_selected==None:
        num_input=input('''Please enter a number to select a category from the bar chart above:
                        enter 'back' to enter a more detailed address,
                        enter 'exit' to exit the program''')
        if num_input.lower()=='back':
            category_list=enter_address()
        elif num_input.lower()=='exit':
            print ('bye')
            sys.exit()
        elif num_input.isnumeric() and 0<int(num_input)<=len(category_list):
            category_selected=category_list[int(num_input)-1]
        else:
            print ('Invalid input')
    print_figure_one_category(category_selected)
    info=info_of_category(category_selected)
    return info


if __name__ == "__main__":
    try:
        create_table()
    except:
        pass
    category_list=enter_address()
    category_selected=select_category(category_list)
    while category_selected!=None:
        num_input=input(('''Please enter a number to select a restaurant from the barchart above:
                        enter 'back' to select another category,
                        enter 'exit' to exit the program'''))
        if num_input.lower()=='back':
            category_selected=(select_category(category_list))
        elif num_input.lower()=='exit':
            print ('bye')
            sys.exit()
        elif num_input.isnumeric() and 0<int(num_input)<=len(category_selected):
            print (info_of_restaurant(category_selected[int(num_input)-1][3]))
        else:
            print ('Invalid input')