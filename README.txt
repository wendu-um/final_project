The program needs both the Yelp Fusion API key and Google Geocoding API key. 
Please supply the keys in a seperate .py file named secret.py by following format:

key='Google Geocoding API key'
key_2='Bearer '+'Yelp Fusion API key

Required Python packages: requests, sqlite3, plotyly

Instruction to interact with the program:
First step: Enter an address that user wants to search for the restaurants nearby.
	    
Second step:The program will display a detailed address. Press any key to confirm
	    the address. Then The program will generate a group bar chart displayed 
            all the categories of restaurants closed to the address with the total 
            review count and the average rating of each category. Each category comes
            with a index number displayed on the bar chart

Third step: Enter the index number of the categories to select one category. Then the
	    program will generate another group bar chart displayed the name, review count
	    and average rating of all the restaurants belong to the selected category Also
            Each restaurant comes with a index number displayed on the bar chart.

Fourth Step: Enter the index number of the restaurants to select one restaurant. Then
             the program will display the detailed information of the selected restaurant.

In all steps described above except the first step, user can enter'back' to go back to 
previous step or enter 'exit' to exit the program.

link to demo video: https://www.youtube.com/watch?v=IxLkf0jqpws&feature=youtu.be